from fastapi import FastAPI
from pydantic import BaseModel
import torch
from torchvision import models, transforms
from PIL import Image
from io import BytesIO
from typing import List
import base64

# Pydantic class for incoming images
class ImageData(BaseModel):
    images: List[str]

app = FastAPI()
model_path = 'resnet18_pretrained.pth'  
model = torch.load(model_path)
model.eval()

# ResNet expects images to go through a standard set of transforms
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

@app.post("/predict/")
async def predict(data: ImageData):
    
    # Decode and transform the image
    decoded_images = [base64.b64decode(img) for img in data.images]
    images = [Image.open(BytesIO(img_data)).convert('RGB') for img_data in decoded_images]
    
    # Batch processing
    batch = torch.stack([transform(image) for image in images])
    with torch.no_grad():
        outputs = model(batch)
    _, predictions = torch.max(outputs, 1)
    return {"class_ids": predictions.tolist()}

# Run the server using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
