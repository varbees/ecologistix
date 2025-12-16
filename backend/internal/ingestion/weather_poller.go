package ingestion

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"time"
)

type WeatherPoller struct {
	baseURL  string
	producer *Producer
	logger   *slog.Logger
}

func NewWeatherPoller(baseURL string, producer *Producer, logger *slog.Logger) *WeatherPoller {
	return &WeatherPoller{
		baseURL:  baseURL,
		producer: producer,
		logger:   logger,
	}
}

func (p *WeatherPoller) Poll(ctx context.Context, lat, lon float64, shipmentID string) {
	url := fmt.Sprintf("%s/forecast?latitude=%f&longitude=%f&hourly=wind_speed_10m,wave_height,precipitation&forecast_days=1", p.baseURL, lat, lon)
	
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		p.logger.Error("Weather API request failed", "error", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		p.logger.Error("Weather API returned non-200 status", "status", resp.StatusCode)
		return
	}

	// Simplified parsing for MVP
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return
	}

	// Check thresholds (mock logic for MVP)
	// In real impl, parse hourly arrays and find max
	
	event := map[string]interface{}{
		"type":        "WEATHER_CHECK",
		"shipment_id": shipmentID,
		"data":        result,
		"timestamp":   time.Now(),
	}

	data, _ := json.Marshal(event)
	p.producer.PublishEvent(ctx, "normal", data)
}
