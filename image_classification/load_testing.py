import requests
import time
import concurrent.futures
import base64

import base64

def base64_encode(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def test_single_request(encoded_image, url):
    start_time = time.time()
    response = requests.post(url, json={"image": encoded_image})
    elapsed_time = time.time() - start_time

    if response.status_code == 200:
        return elapsed_time
    else:
        return None

def load_test(encoded_image, url, number_of_requests):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(test_single_request, encoded_image, url) for _ in range(number_of_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    results = [result for result in results if result is not None]
    return results

def main():
    url = "http://localhost:8888/predict/"  
    sample_image = "sample_images/sample_cat.jpeg"
    encoded_image = base64_encode(sample_image)

    number_of_requests = 200  
    print(f"Starting load test with {number_of_requests} concurrent requests...")

    latencies = load_test(encoded_image, url, number_of_requests)

    average_latency = sum(latencies) / len(latencies)
    print(f"Average latency: {average_latency:.4f} seconds")
    print(f"Min latency: {min(latencies):.4f} seconds")
    print(f"Max latency: {max(latencies):.4f} seconds")
    
if __name__ == "__main__":
    main()
