package main

import (
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"

	"github.com/driftr/ecologistix/backend/internal/orchestrator"
)

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
	
	// Load .env
	if err := godotenv.Load("../../.env"); err != nil {
		logger.Warn("Error loading .env file", "error", err)
	}

	// Redis Connection
	redisHost := os.Getenv("REDIS_HOST")
	redisPort := os.Getenv("REDIS_PORT")
	redisAddr := fmt.Sprintf("%s:%s", redisHost, redisPort)
	if redisHost == "" {
		redisAddr = "localhost:6379"
	}
	
	rdb := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})
	
	if _, err := rdb.Ping(context.Background()).Result(); err != nil {
		logger.Error("Failed to connect to Redis", "error", err)
		os.Exit(1)
	}
	logger.Info("Connected to Redis", "addr", redisAddr)

	// DB Connection (Optional for now, but good to have ready)
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPass := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	
	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPass, dbName)
	
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		logger.Error("Failed to open DB connection", "error", err)
		// Not fatal for Week 5 start, but let's log it
	}
	defer db.Close()

	// Initialize Orchestrator
	orch := orchestrator.NewOrchestrator(rdb, db, logger)

	// Graceful Shutdown Context
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle OS Signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-sigChan
		logger.Info("Shutdown signal received")
		cancel()
	}()

	// Start Orchestrator
	if err := orch.Start(ctx); err != nil && err != context.Canceled {
		logger.Error("Orchestrator failed", "error", err)
		os.Exit(1)
	}
	
	logger.Info("Orchestrator Shutdown Complete")
}
