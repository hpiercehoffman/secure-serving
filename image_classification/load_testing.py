import requests
import time
import concurrent.futures
import base64
import pandas as pd

def base64_encode(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def test_batch_request(encoded_images, url):
    start_time = time.time()
    response = requests.post(url, json={"images": encoded_images})
    elapsed_time = time.time() - start_time

    if response.status_code == 200:
        return elapsed_time, response.json()
    else:
        print(f"Request failed with status code: {response.status_code}") 
        return None

def threaded_batch_test(encoded_images, url, num_threads, requests_per_thread):
   
    with concurrent.futures.ThreadPoolExecutor(max_workers = num_threads) as executor:
        futures = [executor.submit(test_batch_request, encoded_images, url) for _ in range(num_threads * requests_per_thread)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    results = [result for result in results if result is not None]
    return results

def run_threaded_batch_test(url, sample_image, batch_size, num_threads, requests_per_thread):

    encoded_image = base64_encode(sample_image)
    encoded_images = [encoded_image] * batch_size

    print(f"Using batch size of {batch_size} for each request")
    print(f"Starting batch test with {num_threads} threads and {requests_per_thread} requests per thread...")
    test_results = threaded_batch_test(encoded_images, url, num_threads, requests_per_thread)

    latencies = [result[0] for result in test_results]
    average_latency = sum(latencies) / len(latencies)
    print(f"Average latency: {average_latency:.4f} seconds")
    print(f"Min latency: {min(latencies):.4f} seconds")
    print(f"Max latency: {max(latencies):.4f} seconds")
    
def test_vary_thread_count(url, sample_image, batch_size, thread_counts, requests_per_thread):
    results = []

    for num_threads in thread_counts:
        
        print(f"Running test with {num_threads} threads...")
        encoded_image = base64_encode(sample_image)
        encoded_images = [encoded_image] * batch_size

        test_results = threaded_batch_test(encoded_images, url, num_threads, requests_per_thread)

        latencies = [result[0] for result in test_results]
        average_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        results.append({
            "Threads": num_threads,
            "Average Latency": average_latency,
            "Min Latency": min_latency,
            "Max Latency": max_latency
        })
    return pd.DataFrame(results)
    
if __name__ == "__main__":
    url = "http://localhost:9000/predict/"
    sample_image = "sample_images/sample_cat.jpeg"
    batch_size = 2
    thread_counts = [100, 150, 200, 250, 300] 
    requests_per_thread = 2

    enclave_result_df = test_vary_thread_count(url, sample_image, batch_size, thread_counts, requests_per_thread)
    enclave_result_df.to_csv("load_testing_results/enclave_local_batch2_req2_100-300_threads.csv", index=False)
    
