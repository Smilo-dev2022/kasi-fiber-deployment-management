import { RateLimiterRedis } from 'rate-limiter-flexible';
import { createClient } from 'redis';

export function createRateLimiter() {
  const redis = createClient({ url: process.env.REDIS_URL });
  redis.connect().catch(() => {});
  const limiter = new RateLimiterRedis({
    storeClient: redis as any,
    keyPrefix: 'rate',
    points: 100,
    duration: 60
  });
  return limiter;
}

