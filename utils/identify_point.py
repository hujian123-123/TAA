# -*- coding:utf-8 -*-
# @FileName  :identify_point.py
# @Time      :2023/5/5 21:41
# @Author    :Jian
import os
from PIL import Image


import pandas as pd
from torchvision import transforms
import torch.nn.functional as F
import torch

idx_to_labels = {0: 'RestStop', 1: 'TruckOD', 2: 'TruckTrip'}
# 有 GPU 就用 GPU，没有就用 CPU
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

# 训练集图像预处理：缩放裁剪、图像增强、转 Tensor、归一化
train_transform = transforms.Compose([transforms.RandomResizedCrop(224),
                                      transforms.RandomHorizontalFlip(),
                                      transforms.ToTensor(),
                                      transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                                      ])

# 测试集图像预处理-RCTN：缩放、裁剪、转 Tensor、归一化
test_transform = transforms.Compose([transforms.Resize(256),
                                     transforms.CenterCrop(224),
                                     transforms.ToTensor(),
                                     transforms.Normalize(
                                         mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
                                     ])

model = torch.load(r'./files/best-0.980.pth')

# model = torch.load(r'./files/best-0.980.pth',map_location=torch.device('cpu'))
model = model.eval().to(device)


def identify_gps_point(clustering_reslut, img_floder_path):
    img_list = os.listdir(img_floder_path)
    img_list.sort(key = lambda x: int(x.split('_')[1].strip('.png')))
    img_list = img_list[:len(clustering_reslut)]
    res = []
    for img_path in img_list:
        img_path = img_floder_path + '/'+ img_path
        img_pil = Image.open(img_path).convert("RGB")
        input_img = test_transform(img_pil)  # 预处理
        input_img = input_img.unsqueeze(0).to(device)
        # 执行前向预测，得到所有类别的 logit 预测分数
        pred_logits = model(input_img)
        pred_softmax = F.softmax(pred_logits, dim=1)  # 对 logit 分数做 softmax 运算
        top_ = torch.topk(pred_softmax, 1)  # 取置信度最大的 n 个结果
        top_ = top_[1].cpu().detach().numpy().squeeze()
        one_img_data = [img_path, int(top_), idx_to_labels[int(top_)]]
        res.append(one_img_data)
    res.sort(key=lambda x: int(x[0].split('_')[1].strip('.png')))

    result_data = pd.concat([clustering_reslut, pd.DataFrame(res, columns=['img_path', 'label', 'category'])], axis=1)
    return result_data
