import requests
import time
import concurrent.futures
import base64

import base64

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

def run_load_test_batch(url, sample_image, batch_size, num_threads, requests_per_thread):

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
    
if __name__ == "__main__":
    url = "http://localhost:9000/predict/"  
    sample_image = "sample_images/sample_cat.jpeg"
    batch_size = 20
    num_threads = 100
    requests_per_thread = 2
    run_load_test_batch(url, sample_image, batch_size, num_threads, requests_per_thread)
