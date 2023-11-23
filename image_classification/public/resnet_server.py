from fastapi import FastAPI
from pydantic import BaseModel
import torch
from torchvision import models, transforms
from PIL import Image
from io import BytesIO
import base64

# Pydantic class for incoming images
class ImageData(BaseModel):
    image: str 

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
    image_data = base64.b64decode(data.image)
    image = Image.open(BytesIO(image_data)).convert('RGB')
    image_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model(image_tensor)
    
    _, predicted = torch.max(outputs, 1)
    return {"class_id": predicted.item()}

# Run the server using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
