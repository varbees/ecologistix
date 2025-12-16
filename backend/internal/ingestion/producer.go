package ingestion

import (
	"context"
	"fmt"

	"github.com/redis/go-redis/v9"
)

type Producer struct {
	redis *redis.Client
}

func NewProducer(redisClient *redis.Client) *Producer {
	return &Producer{
		redis: redisClient,
	}
}

func (p *Producer) PublishEvent(ctx context.Context, priority string, eventJSON []byte) error {
	queueName := fmt.Sprintf("event:queue:%s_priority", priority)
	return p.redis.LPush(ctx, queueName, eventJSON).Err()
}
