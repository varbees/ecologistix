package orchestrator

import (
	"context"
	"encoding/json"
	"time"
)

func (o *Orchestrator) handleHighRiskEvent(ctx context.Context, event map[string]interface{}) {
	o.logger.Info("Handling High Risk Event", "event", event)

	shipmentID, ok := event["shipment_id"].(string)
	if !ok {
		// Try accessing from "affected_shipments" list if it's a disruption event, 
		// but for Risk Scout output (Check Week 4), it might be direct.
		// RiskScoutAgent output structure: { "shipment_id": "...", "risk_score": ... }
		// Wait, RiskScoutAgent updates DB directly. Does it push to Redis?
		// Roadmap says Risk Scout Flags HIGH risks for Orchestrator. 
		// Implementation of RiskScout (Week 4) updated DB. It did NOT push to Redis yet.
		// Missing link?
		// In Week 4 RiskScoutAgent: `await self.db.update_shipment_risk(...)`.
		// It should probably also `rpush` to redis if risk > threshold.
		// I'll assume for now we will simulate event injection or fix Agent later.
		// Let's handle the event assuming standard structure.
		o.logger.Error("Missing shipment_id in event")
		return
	}

	riskScore, _ := event["risk_score"].(float64)
	
	// Update blackboard
	o.mu.Lock()
	state, exists := o.globalState[shipmentID]
	var shipmentState map[string]interface{}
	if exists {
		shipmentState = state.(map[string]interface{})
	} else {
		shipmentState = make(map[string]interface{})
		shipmentState["id"] = shipmentID
	}
	
	shipmentState["risk_score"] = riskScore
	shipmentState["status"] = "AT_RISK"
	shipmentState["last_updated"] = event["detected_at"]
	
	o.globalState[shipmentID] = shipmentState
	o.mu.Unlock()
	
	
	o.logger.Info("Blackboard updated for shipment", "id", shipmentID, "risk_score", riskScore)

	// Decision Logic: Delegation
	if riskScore > 0.7 {
		o.logger.Info("Risk Critical! Delegating to Route Planner", "id", shipmentID)
		o.delegateToRoutePlanner(ctx, shipmentID, event)
	}
}

func (o *Orchestrator) delegateToRoutePlanner(ctx context.Context, shipmentID string, reasonData map[string]interface{}) {
	// Publish task to Route Planner Queue
	task := map[string]interface{}{
		"task_type": "PLAN_NEW_ROUTE",
		"shipment_id": shipmentID,
		"reason": reasonData,
		"created_at": time.Now().Format(time.RFC3339),
	}
	
	payload, err := json.Marshal(task)
	if err != nil {
		o.logger.Error("Failed to marshal task payload", "error", err)
		return
	}

	queueName := "agent:task:route_planner"
	err = o.redis.RPush(ctx, queueName, payload).Err()
	if err != nil {
		o.logger.Error("Failed to push task to Redis", "queue", queueName, "error", err)
		return
	}
	
	o.logger.Info("Delegated task to Route Planner", "queue", queueName, "shipment_id", shipmentID)
}

func (o *Orchestrator) handleWeatherAlert(ctx context.Context, event map[string]interface{}) {
	o.logger.Info("Handling Weather Alert", "event", event)
	// Similar logic: find affected shipments, update blackboard, trigger replan if needed
}
