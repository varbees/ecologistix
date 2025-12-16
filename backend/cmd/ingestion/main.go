package main

import (
	"context"
	"os"

	"github.com/driftr/ecologistix/backend/internal/ingestion"
	"github.com/driftr/ecologistix/backend/internal/logger"
	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
)

func main() {
	_ = godotenv.Load("../.env") // Load from root
	logger := logger.Setup()
	logger.Info("Ingestion Service Starting")

	redisAddr := os.Getenv("REDIS_HOST") + ":" + os.Getenv("REDIS_PORT")
	redisClient := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	producer := ingestion.NewProducer(redisClient)

	// AIS Listener
	aisKey := os.Getenv("AIS_API_KEY") 
	aisListener := ingestion.NewAISListener(aisKey, producer, logger)

	// Weather Poller (Example usage)
	// weatherPoller := ingestion.NewWeatherPoller(os.Getenv("OPEN_METEO_BASE_URL"), producer, logger)

	// News Aggregator (Example usage)
	// newsAggregator := ingestion.NewNewsAggregator(os.Getenv("NEWSAPI_KEY"), producer, logger)


	// Context for cancellation
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start AIS Listener in goroutine
	go aisListener.Listen(ctx)

	// Initial check to keep main alive (Production would use signal handling)
	select {}
}
