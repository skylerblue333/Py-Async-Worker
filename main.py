import asyncio
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AsyncWorker')

async def process_task(task_id, duration):
    logger.info(f"Task {task_id}: Starting (duration: {duration}s)")
    await asyncio.sleep(duration)
    logger.info(f"Task {task_id}: Completed")
    return f"Result of {task_id}"

async def main():
    logger.info("Worker pool initialized. Waiting for tasks...")
    
    tasks = []
    for i in range(5):
        duration = random.uniform(0.5, 2.0)
        tasks.append(asyncio.create_task(process_task(f"T-{i}", duration)))
        
    results = await asyncio.gather(*tasks)
    logger.info(f"All tasks completed. Results: {results}")

if __name__ == "__main__":
    asyncio.run(main())