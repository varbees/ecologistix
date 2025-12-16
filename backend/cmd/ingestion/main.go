package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"

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

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	<-sigChan
	logger.Info("Shutdown signal received")
	cancel() // Cancel context to stop listeners

	// Give components time to cleanup if needed (e.g. close Redis connections)
	// In production, use a timeout with context
	if err := redisClient.Close(); err != nil {
		logger.Error("Failed to close Redis client", "error", err)
	}
	
	logger.Info("Ingestion Service Stopped")
}
