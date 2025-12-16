package ingestion

import (
	"context"
	"encoding/json"
	"log/slog"
	"time"

	"github.com/gorilla/websocket"
)

const AISStreamURL = "wss://stream.aisstream.io/v0/stream"

type AISMessage struct {
	MessageType string      `json:"MessageType"`
	MetaData    AISMetaData `json:"MetaData"`
	Message     struct {
		PositionReport *PositionReport `json:"PositionReport"`
	} `json:"Message"`
}

type AISMetaData struct {
	MMSI             int     `json:"MMSI"`
	ShipName         string  `json:"ShipName"`
	Latitude         float64 `json:"latitude"`
	Longitude        float64 `json:"longitude"`
	TimeUTC          string  `json:"time_utc"`
}

type PositionReport struct {
	Cog        float64 `json:"Cog"`
	Sog        float64 `json:"Sog"`
	TrueHeading int    `json:"TrueHeading"`
}

type AISListener struct {
	apiKey   string
	producer *Producer
	logger   *slog.Logger
}

func NewAISListener(apiKey string, producer *Producer, logger *slog.Logger) *AISListener {
	return &AISListener{
		apiKey:   apiKey,
		producer: producer,
		logger:   logger,
	}
}

func (l *AISListener) Listen(ctx context.Context) {
	conn, _, err := websocket.DefaultDialer.Dial(AISStreamURL, nil)
	if err != nil {
		l.logger.Error("Failed to connect to AIS stream", "error", err)
		return
	}
	defer conn.Close()

	l.logger.Info("Connected to AIS stream")

	// Subscribe message
	subMsg := map[string]interface{}{
		"APIKey":          l.apiKey,
		"BoundingBoxes":   [][][2]float64{{{-90, -180}, {90, 180}}}, // Global
		"FilterMessageTypes": []string{"PositionReport"},
	}
	if err := conn.WriteJSON(subMsg); err != nil {
		l.logger.Error("Failed to subscribe", "error", err)
		return
	}

	for {
		select {
		case <-ctx.Done():
			return
		default:
			_, message, err := conn.ReadMessage()
			if err != nil {
				l.logger.Error("Read error", "error", err)
				time.Sleep(5 * time.Second) // Reconnect logic placeholder
				return
			}

			var aisMsg AISMessage
			if err := json.Unmarshal(message, &aisMsg); err != nil {
				continue
			}

			if aisMsg.MessageType == "PositionReport" {
				l.processMessage(ctx, aisMsg)
			}
		}
	}
}

func (l *AISListener) processMessage(ctx context.Context, msg AISMessage) {
	// Simple normalization
	event := map[string]interface{}{
		"type":        "SHIPMENT_UPDATE",
		"mmsi":        msg.MetaData.MMSI,
		"lat":         msg.MetaData.Latitude,
		"lon":         msg.MetaData.Longitude,
		"speed":       msg.Message.PositionReport.Sog,
		"heading":     msg.Message.PositionReport.TrueHeading,
		"timestamp":   time.Now().Format(time.RFC3339),
		"source":      "AIS",
	}

	data, _ := json.Marshal(event)
	// Push to normal priority queue
	if err := l.producer.PublishEvent(ctx, "normal", data); err != nil {
		l.logger.Error("Failed to push event", "error", err)
	}
}
