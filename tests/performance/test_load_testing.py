"""
Load testing for AI Executive Suite
"""

import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import random

from tests.factories import UserFactory, DecisionFactory


@pytest.mark.performance
class TestAPILoadTesting:
    """Load testing for API endpoints"""
    
    def test_decision_endpoint_load(self, client, sample_user):
        """Test decision endpoint under load"""
        results = []
        errors = []
        
        def make_decision_request(request_id):
            """Make a single decision request"""
            try:
                with client.session_transaction() as sess:
                    sess['user_id'] = sample_user.id
                
                with patch('services.ai_integration.AIIntegrationService') as mock_ai:
                    mock_response = Mock()
                    mock_response.decision = f"Load test decision {request_id}"
                    mock_response.rationale = f"Load test rationale {request_id}"
                    mock_response.confidence_score = random.uniform(0.7, 0.9)
                    mock_response.priority = random.choice(['low', 'medium', 'high'])
                    mock_response.category = random.choice(['strategic', 'operational', 'financial'])
                    mock_response.risk_level = random.choice(['low', 'medium', 'high'])
                    
                    mock_ai.return_value.generate_executive_response.return_value = mock_response
                    
                    start_time = time.time()
                    
                    response = client.post('/api/ceo/decision', json={
                        'context': f'Load test context {request_id}',
                        'options': ['Option A', 'Option B', 'Option C']
                    })
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    return {
                        'request_id': request_id,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'success': response.status_code == 200
                    }
            
            except Exception as e:
                return {
                    'request_id': request_id,
                    'error': str(e),
                    'success': False
                }
        
        # Test parameters
        num_requests = 50
        max_workers = 10
        
        start_time = time.time()
        
        # Execute load test
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(make_decision_request, i) 
                for i in range(num_requests)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    results.append(result)
                else:
                    errors.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        success_count = len(results)
        error_count = len(errors)
        success_rate = success_count / num_requests
        
        response_times = [r['response_time'] for r in results if 'response_time' in r]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = max_response_time = 0
        
        requests_per_second = num_requests / total_time
        
        # Performance assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below threshold"
        assert avg_response_time < 5.0, f"Average response time {avg_response_time:.2f}s too high"
        assert p95_response_time < 10.0, f"95th percentile response time {p95_response_time:.2f}s too high"
        assert requests_per_second >= 5.0, f"Throughput {requests_per_second:.2f} req/s too low"
        
        # Print performance metrics
        print(f"\nLoad Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Successful Requests: {success_count}")
        print(f"Failed Requests: {error_count}")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Requests/Second: {requests_per_second:.2f}")
        print(f"Average Response Time: {avg_response_time:.3f}s")
        print(f"Median Response Time: {median_response_time:.3f}s")
        print(f"95th Percentile Response Time: {p95_response_time:.3f}s")
        print(f"Max Response Time: {max_response_time:.3f}s")
    
    def test_analytics_endpoint_load(self, client, sample_user, sample_decisions):
        """Test analytics endpoint under load"""
        results = []
        
        def make_analytics_request(request_id):
            """Make a single analytics request"""
            try:
                with client.session_transaction() as sess:
                    sess['user_id'] = sample_user.id
                
                with patch('services.analytics.AnalyticsService') as mock_analytics:
                    mock_data = Mock()
                    mock_data.total_decisions = random.randint(50, 200)
                    mock_data.decisions_by_executive = {
                        'ceo': random.randint(10, 50),
                        'cto': random.randint(10, 50),
                        'cfo': random.randint(10, 50)
                    }
                    mock_data.average_confidence_score = random.uniform(0.7, 0.9)
                    mock_data.implementation_rate = random.uniform(0.6, 0.9)
                    
                    mock_analytics.return_value.generate_decision_analytics.return_value = mock_data
                    
                    start_time = time.time()
                    
                    response = client.get('/api/analytics/decisions', query_string={
                        'days': random.choice([7, 30, 90]),
                        'executive_types': 'ceo,cto,cfo'
                    })
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    return {
                        'request_id': request_id,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'success': response.status_code == 200
                    }
            
            except Exception as e:
                return {
                    'request_id': request_id,
                    'error': str(e),
                    'success': False
                }
        
        # Test parameters
        num_requests = 30
        max_workers = 5
        
        start_time = time.time()
        
        # Execute load test
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(make_analytics_request, i) 
                for i in range(num_requests)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        success_rate = len(successful_results) / num_requests
        
        response_times = [r['response_time'] for r in successful_results]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Performance assertions
        assert success_rate >= 0.95, f"Analytics success rate {success_rate:.2%} below threshold"
        assert avg_response_time < 3.0, f"Analytics average response time {avg_response_time:.2f}s too high"
    
    def test_document_upload_load(self, client, sample_user):
        """Test document upload endpoint under load"""
        results = []
        
        def upload_document(request_id):
            """Upload a single document"""
            try:
                with client.session_transaction() as sess:
                    sess['user_id'] = sample_user.id
                
                # Create temporary file content
                file_content = f"Test document content for load test {request_id}\n" * 100
                
                with patch('services.document_processing.DocumentProcessingService') as mock_service:
                    mock_document = Mock()
                    mock_document.id = f'doc_{request_id}'
                    mock_document.filename = f'load_test_{request_id}.txt'
                    mock_document.file_type = 'txt'
                    mock_document.document_type = 'technical'
                    
                    mock_service.return_value.upload_document.return_value = mock_document
                    
                    start_time = time.time()
                    
                    response = client.post('/api/documents/upload', data={
                        'file': (file_content.encode(), f'load_test_{request_id}.txt'),
                        'document_type': 'technical',
                        'sensitivity_level': 'internal'
                    })
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    return {
                        'request_id': request_id,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'success': response.status_code == 200
                    }
            
            except Exception as e:
                return {
                    'request_id': request_id,
                    'error': str(e),
                    'success': False
                }
        
        # Test parameters
        num_uploads = 20
        max_workers = 5
        
        # Execute load test
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(upload_document, i) 
                for i in range(num_uploads)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        success_rate = len(successful_results) / num_uploads
        
        response_times = [r['response_time'] for r in successful_results]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Performance assertions
        assert success_rate >= 0.90, f"Upload success rate {success_rate:.2%} below threshold"
        assert avg_response_time < 10.0, f"Upload average response time {avg_response_time:.2f}s too high"


@pytest.mark.performance
class TestDatabasePerformance:
    """Database performance testing"""
    
    def test_decision_query_performance(self, db_session, sample_user):
        """Test decision query performance with large dataset"""
        # Create large dataset
        decisions = []
        batch_size = 100
        total_decisions = 1000
        
        start_time = time.time()
        
        for i in range(0, total_decisions, batch_size):
            batch_decisions = []
            for j in range(batch_size):
                if i + j >= total_decisions:
                    break
                
                decision = DecisionFactory.build(
                    user_id=sample_user.id,
                    title=f'Performance Test Decision {i+j}',
                    executive_type=random.choice(['ceo', 'cto', 'cfo']),
                    priority=random.choice(['low', 'medium', 'high']),
                    status=random.choice(['pending', 'in_progress', 'completed']),
                    confidence_score=random.uniform(0.5, 1.0)
                )
                batch_decisions.append(decision)
            
            db_session.add_all(batch_decisions)
            db_session.commit()
        
        insert_time = time.time() - start_time
        
        # Test various query patterns
        query_tests = [
            {
                'name': 'All user decisions',
                'query': lambda: db_session.query(Decision).filter_by(user_id=sample_user.id).all()
            },
            {
                'name': 'CEO decisions only',
                'query': lambda: db_session.query(Decision).filter_by(
                    user_id=sample_user.id, executive_type='ceo'
                ).all()
            },
            {
                'name': 'High priority decisions',
                'query': lambda: db_session.query(Decision).filter_by(
                    user_id=sample_user.id, priority='high'
                ).all()
            },
            {
                'name': 'Completed decisions',
                'query': lambda: db_session.query(Decision).filter_by(
                    user_id=sample_user.id, status='completed'
                ).all()
            },
            {
                'name': 'Count all decisions',
                'query': lambda: db_session.query(Decision).filter_by(user_id=sample_user.id).count()
            }
        ]
        
        query_results = []
        
        for test in query_tests:
            start_time = time.time()
            result = test['query']()
            end_time = time.time()
            query_time = end_time - start_time
            
            query_results.append({
                'name': test['name'],
                'query_time': query_time,
                'result_count': len(result) if hasattr(result, '__len__') else result
            })
        
        # Performance assertions
        assert insert_time < 30.0, f"Insert time {insert_time:.2f}s too high for {total_decisions} records"
        
        for result in query_results:
            assert result['query_time'] < 2.0, f"Query '{result['name']}' took {result['query_time']:.3f}s"
        
        # Print performance metrics
        print(f"\nDatabase Performance Results:")
        print(f"Insert Time for {total_decisions} records: {insert_time:.2f}s")
        for result in query_results:
            print(f"{result['name']}: {result['query_time']:.3f}s ({result['result_count']} results)")
    
    def test_concurrent_database_access(self, db_session, sample_user):
        """Test concurrent database access performance"""
        results = []
        
        def database_operation(thread_id):
            """Perform database operations in a thread"""
            try:
                from models import Decision
                
                # Create decision
                decision = Decision(
                    user_id=sample_user.id,
                    executive_type='ceo',
                    title=f'Concurrent Test Decision {thread_id}',
                    context=f'Concurrent test context {thread_id}',
                    decision=f'Concurrent test decision {thread_id}',
                    rationale=f'Concurrent test rationale {thread_id}'
                )
                
                start_time = time.time()
                
                db_session.add(decision)
                db_session.commit()
                
                # Query decisions
                decisions = db_session.query(Decision).filter_by(user_id=sample_user.id).all()
                
                end_time = time.time()
                operation_time = end_time - start_time
                
                return {
                    'thread_id': thread_id,
                    'operation_time': operation_time,
                    'decisions_count': len(decisions),
                    'success': True
                }
            
            except Exception as e:
                return {
                    'thread_id': thread_id,
                    'error': str(e),
                    'success': False
                }
        
        # Test parameters
        num_threads = 10
        
        start_time = time.time()
        
        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(database_operation, i) 
                for i in range(num_threads)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        success_rate = len(successful_results) / num_threads
        
        operation_times = [r['operation_time'] for r in successful_results]
        avg_operation_time = statistics.mean(operation_times) if operation_times else 0
        
        # Performance assertions
        assert success_rate >= 0.90, f"Concurrent DB success rate {success_rate:.2%} below threshold"
        assert avg_operation_time < 5.0, f"Average DB operation time {avg_operation_time:.2f}s too high"
        assert total_time < 15.0, f"Total concurrent operation time {total_time:.2f}s too high"


@pytest.mark.performance
class TestMemoryPerformance:
    """Memory usage performance testing"""
    
    def test_memory_usage_under_load(self, client, sample_user):
        """Test memory usage under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        results = []
        
        for i in range(100):
            with client.session_transaction() as sess:
                sess['user_id'] = sample_user.id
            
            with patch('services.ai_integration.AIIntegrationService') as mock_ai:
                # Create large mock response
                mock_response = Mock()
                mock_response.decision = "Large decision content " * 100
                mock_response.rationale = "Large rationale content " * 100
                mock_response.confidence_score = 0.8
                mock_response.priority = "medium"
                mock_response.category = "strategic"
                mock_response.risk_level = "low"
                
                mock_ai.return_value.generate_executive_response.return_value = mock_response
                
                response = client.post('/api/ceo/decision', json={
                    'context': f'Memory test context {i}' * 50  # Large context
                })
                
                results.append(response.status_code)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory assertions
        assert memory_increase < 100, f"Memory increase {memory_increase:.2f}MB too high"
        assert all(status == 200 for status in results), "Some requests failed during memory test"
        
        print(f"\nMemory Performance Results:")
        print(f"Initial Memory: {initial_memory:.2f}MB")
        print(f"Final Memory: {final_memory:.2f}MB")
        print(f"Memory Increase: {memory_increase:.2f}MB")
    
    def test_large_dataset_memory_efficiency(self, db_session, sample_user):
        """Test memory efficiency with large datasets"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        large_dataset_size = 5000
        
        # Use batch processing to manage memory
        batch_size = 500
        
        for i in range(0, large_dataset_size, batch_size):
            batch_decisions = []
            
            for j in range(batch_size):
                if i + j >= large_dataset_size:
                    break
                
                decision = DecisionFactory.build(
                    user_id=sample_user.id,
                    title=f'Memory Test Decision {i+j}',
                    context='Memory test context ' * 20,  # Larger content
                    decision='Memory test decision ' * 20,
                    rationale='Memory test rationale ' * 20
                )
                batch_decisions.append(decision)
            
            db_session.add_all(batch_decisions)
            db_session.commit()
            
            # Clear batch from memory
            del batch_decisions
        
        # Query large dataset
        from models import Decision
        all_decisions = db_session.query(Decision).filter_by(user_id=sample_user.id).all()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory efficiency assertions
        assert len(all_decisions) == large_dataset_size, f"Expected {large_dataset_size} decisions, got {len(all_decisions)}"
        assert memory_increase < 200, f"Memory increase {memory_increase:.2f}MB too high for large dataset"
        
        print(f"\nLarge Dataset Memory Results:")
        print(f"Dataset Size: {large_dataset_size} records")
        print(f"Initial Memory: {initial_memory:.2f}MB")
        print(f"Final Memory: {final_memory:.2f}MB")
        print(f"Memory Increase: {memory_increase:.2f}MB")
        print(f"Memory per Record: {memory_increase/large_dataset_size:.4f}MB")


@pytest.mark.performance
class TestCachePerformance:
    """Cache performance testing"""
    
    def test_redis_cache_performance(self, mock_redis):
        """Test Redis cache performance"""
        from services.analytics import AnalyticsService
        
        config = {
            'analytics': {
                'cache_enabled': True,
                'cache_ttl': 300
            }
        }
        
        service = AnalyticsService(config)
        service.redis_client = mock_redis
        
        # Test cache operations
        cache_operations = []
        
        for i in range(100):
            start_time = time.time()
            
            # Cache set operation
            cache_key = f'analytics:test:{i}'
            cache_data = {'test_data': f'value_{i}', 'timestamp': time.time()}
            
            mock_redis.set(cache_key, str(cache_data))
            
            # Cache get operation
            cached_result = mock_redis.get(cache_key)
            
            end_time = time.time()
            operation_time = end_time - start_time
            
            cache_operations.append(operation_time)
        
        avg_cache_time = statistics.mean(cache_operations)
        max_cache_time = max(cache_operations)
        
        # Cache performance assertions
        assert avg_cache_time < 0.001, f"Average cache operation time {avg_cache_time:.4f}s too high"
        assert max_cache_time < 0.01, f"Max cache operation time {max_cache_time:.4f}s too high"
        
        print(f"\nCache Performance Results:")
        print(f"Average Cache Operation Time: {avg_cache_time:.4f}s")
        print(f"Max Cache Operation Time: {max_cache_time:.4f}s")
        print(f"Cache Operations per Second: {1/avg_cache_time:.0f}")


if __name__ == "__main__":
    pytest.main([__file__])