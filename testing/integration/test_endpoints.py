import boto3
import json
import time
import unittest
import numpy as np

# Initialize the SageMaker client
client = boto3.client('sagemaker-runtime', 'us-east-1')

endpoint_name_1 = "defenderImageAnalyzerEndpointC5i"
endpoint_name_2 = "defenderImageAnalyzerEndpointC6i2x"
bucket = "defender-image-reverse-search-4242"
key = "trudeau.jpg"
content_type = "application/json"

class TestImageAnalyzerEndpoint(unittest.TestCase):
    def setUp(self):
        """ Set up test-wide variables before any test runs """
        self.payload = {
            "bucket": bucket,
            "key": key
        }
        self.result_1 = self.invoke_endpoint(endpoint_name_1) # Endpoint 1
        self.result_2 = self.invoke_endpoint(endpoint_name_2) # Endpoint 2
    
    def invoke_endpoint(self, endpoint_name):
        start_time = time.time()
        # Make inference request
        response = client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType=content_type,
            Body=json.dumps(self.payload).encode('utf-8')
        )
        # Decode result
        result = json.loads(response['Body'].read().decode())
        # Stop timer
        elapsed_time = time.time() - start_time
        # Check for error in response
        if 'error' in result:
            self.fail(f"Error in invoke_endpoint: {result}")
        print(f"Endpoint {endpoint_name} took {elapsed_time:.2f} seconds, # faces: {len(result)}")
        return result
    
    def cosine_similarity(self, vec1, vec2):
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        return dot_product / (norm_vec1 * norm_vec2)

    def test_face_detection(self):
        """ Test endpoint for expected face results """
        # Assertions
        self.assertEqual(len(self.result_1), 1, "Expected 1 face detected")
        self.assertEqual(len(self.result_2), 1, "Expected 1 face detected")
        
    def test_model_dimension(self):
        """ Test endpoint for expected dimension results """
        # Assertions
        self.assertEqual(len(self.result_1[0]["embedding"]), 512, "Expected 512 embedding dimensions")
        self.assertEqual(len(self.result_2[0]["embedding"]), 512, "Expected 512 embedding dimensions")
        
    def test_model_consistency(self):
        """ Test endpoint for expected embedding by Calculating model embdeings for a known image and comapre the two"""
        
        # Load embedings for a known image 
        with open("testing/assets/trudeau_img_embedding.json", "r") as file:
            embedding = json.load(file)
            
        cosine_similarity_1 = self.cosine_similarity(embedding, self.result_1[0]["embedding"])  # Endpoint 1
        cosine_similarity_2 = self.cosine_similarity(embedding, self.result_2[0]["embedding"])  # Endpoint 2
        
        # Assertions
        self.assertGreaterEqual(cosine_similarity_1, 0.75, "Expected embedding")
        self.assertGreaterEqual(cosine_similarity_2, 0.75, "Expected embedding")
        
            
        
        
        
