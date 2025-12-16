package ingestion

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"time"
)

type NewsAggregator struct {
	apiKey   string
	producer *Producer
	logger   *slog.Logger
}

func NewNewsAggregator(apiKey string, producer *Producer, logger *slog.Logger) *NewsAggregator {
	return &NewsAggregator{
		apiKey:   apiKey,
		producer: producer,
		logger:   logger,
	}
}

func (n *NewsAggregator) FetchNews(ctx context.Context) {
	// Example query
	url := fmt.Sprintf("https://newsapi.org/v2/everything?q=supply+chain&apiKey=%s", n.apiKey)

	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		n.logger.Error("News API request failed", "error", err)
		return
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		n.logger.Error("Failed to decode news response", "error", err)
		return
	}

	if articles, ok := result["articles"].([]interface{}); ok {
		for _, art := range articles {
			// Publish relevant news
			event := map[string]interface{}{
				"type":    "NEWS_ALERT",
				"payload": art,
				"timestamp": time.Now(),
			}
			data, _ := json.Marshal(event)
			n.producer.PublishEvent(ctx, "normal", data)
		}
	}
}
