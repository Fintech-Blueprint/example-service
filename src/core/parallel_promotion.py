"""
Parallel Promotion Manager for handling concurrent service promotions.
"""
from typing import List, Dict, Set
from datetime import datetime
import asyncio
import logging
from collections import defaultdict

class ParallelPromotionManager:
    def __init__(self):
        self.service_dependencies = defaultdict(set)
        self.active_promotions = set()
        self.promotion_locks = defaultdict(asyncio.Lock)
        self.logger = logging.getLogger(__name__)

    async def register_service_dependencies(self, service: str, dependencies: List[str]):
        """Register service dependencies for promotion ordering."""
        self.service_dependencies[service] = set(dependencies)

    def _get_independent_services(self, services: List[str]) -> Set[str]:
        """Find services that can be promoted independently."""
        independent = set()
        for service in services:
            deps = self.service_dependencies[service]
            if not deps.intersection(set(services)):
                independent.add(service)
        return independent

    async def promote_services(self, services: List[str]) -> Dict[str, bool]:
        """
        Promote multiple services in parallel when possible.
        Returns a dictionary of service names to promotion success status.
        """
        results = {}
        
        # Find independent services that can be promoted in parallel
        independent = self._get_independent_services(services)
        dependent = set(services) - independent
        
        # Promote independent services in parallel
        if independent:
            promotion_tasks = []
            for service in independent:
                task = asyncio.create_task(self._promote_single_service(service))
                promotion_tasks.append((service, task))
            
            for service, task in promotion_tasks:
                try:
                    success = await task
                    results[service] = success
                except Exception as e:
                    self.logger.error(f"Error promoting {service}: {str(e)}")
                    results[service] = False
        
        # Promote dependent services sequentially
        for service in dependent:
            success = await self._promote_single_service(service)
            results[service] = success
        
        return results

    async def _promote_single_service(self, service: str) -> bool:
        """
        Promote a single service with locking to prevent conflicts.
        """
        async with self.promotion_locks[service]:
            if service in self.active_promotions:
                self.logger.warning(f"Service {service} is already being promoted")
                return False
            
            try:
                self.active_promotions.add(service)
                
                # Validate dependencies are already promoted
                deps = self.service_dependencies[service]
                if not self._validate_dependencies(deps):
                    self.logger.error(f"Dependencies not met for {service}")
                    return False
                
                # Perform the actual promotion
                success = await self._execute_promotion(service)
                
                if success:
                    self.logger.info(f"Successfully promoted {service}")
                    return True
                else:
                    self.logger.error(f"Failed to promote {service}")
                    return False
                    
            finally:
                self.active_promotions.remove(service)

    def _validate_dependencies(self, dependencies: Set[str]) -> bool:
        """Validate that all dependencies are promoted."""
        # Implementation would check the current state of each dependency
        return True  # Simplified for POC

    async def _execute_promotion(self, service: str) -> bool:
        """Execute the actual promotion process for a service."""
        try:
            # Actual promotion logic would go here
            await asyncio.sleep(1)  # Simulating work
            return True
        except Exception as e:
            self.logger.error(f"Promotion execution failed for {service}: {str(e)}")
            return False

    async def get_promotion_status(self, service: str) -> Dict[str, any]:
        """Get the current promotion status of a service."""
        return {
            "service": service,
            "active": service in self.active_promotions,
            "dependencies": list(self.service_dependencies[service]),
            "timestamp": datetime.utcnow().isoformat()
        }