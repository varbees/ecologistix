package orchestrator

import (
	"context"
	"database/sql"
	"encoding/json"
	"log/slog"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
)

type AgentType string

const (
	RiskScout     AgentType = "RISK_SCOUT"
	RoutePlanner  AgentType = "ROUTE_PLANNER"
	CarbonAuditor AgentType = "CARBON_AUDITOR"
	RAGEngine     AgentType = "RAG_ENGINE"
)

type Orchestrator struct {
	redis          *redis.Client
	db             *sql.DB
	logger         *slog.Logger
	mu             sync.RWMutex
	globalState    map[string]interface{} // Blackboard
	agentResponses map[string]chan interface{}
	maxConcurrency int
}

func NewOrchestrator(redisClient *redis.Client, db *sql.DB, logger *slog.Logger) *Orchestrator {
	return &Orchestrator{
		redis:          redisClient,
		db:             db,
		logger:         logger,
		globalState:    make(map[string]interface{}),
		agentResponses: make(map[string]chan interface{}),
		maxConcurrency: 5,
	}
}

// Start Main event loop
func (o *Orchestrator) Start(ctx context.Context) error {
	o.logger.Info("Orchestrator Service Loop Starting...")
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			o.logger.Info("Orchestrator Context Done, stopping...")
			return ctx.Err()
		case <-ticker.C:
			// Process events from queue
			o.processEventQueue(ctx)
		}
	}
}

func (o *Orchestrator) processEventQueue(ctx context.Context) {
	// Pop event from Redis queue
	// Using BLPOP with timeout could be better, but roadmap used polling with ticker/LPop
	// Let's stick to LPOP for simplicity or BLPOP if we move blocking logic. 
    // Roadmap example used LPop.
	
	// Priority 1: High Priority
	event, err := o.redis.LPop(ctx, "event:queue:high_priority").Result()
	if err == redis.Nil {
		// Priority 2: Normal Priority
		event, err = o.redis.LPop(ctx, "event:queue:normal_priority").Result()
	}
	
	if err == redis.Nil {
		return // No events
	}
	if err != nil {
		o.logger.Error("Error reading queue", "error", err)
		return
	}

	o.logger.Info("Received Event", "payload", event)

	var eventData map[string]interface{}
	if err := json.Unmarshal([]byte(event), &eventData); err != nil {
		o.logger.Error("Failed to unmarshal event", "error", err)
		return
	}

	// Route to handler based on event type
	eventType, ok := eventData["event_type"].(string)
	if !ok {
		o.logger.Warn("Event missing event_type", "event", eventData)
		return
	}

	switch eventType {
	case "HIGH_RISK_DETECTED":
		o.handleHighRiskEvent(ctx, eventData)
	case "WEATHER_ALERT":
		o.handleWeatherAlert(ctx, eventData)
	default:
		o.logger.Info("Unhandled event type", "type", eventType)
	}
}
