# PIORS
The repo of the Personalized Intelligent Outpatient Reception System (PIORS) and the Service Flow aware Medical Scenario Simulation (SFMSS))

- [Paper](https://arxiv.org/abs/2411.13902)
- The code and other resources will be uploaded soon.

## Overview
In China, receptionist nurses face overwhelming workloads in outpatient settings, limiting their time and attention for each patient and ultimately reducing service quality. 
We present the **Personalized Intelligent Outpatient Reception System (PIORS)**. This system integrates an LLM-based reception nurse and a collaboration between LLM and hospital information system (HIS) into real outpatient reception setting, aiming to deliver personalized, high-quality, and efficient reception services. Additionally, to enhance the performance of LLMs in real-world healthcare scenarios, we propose a medical conversational data generation framework named **Service Flow aware Medical Scenario Simulation (SFMSS)**, aiming to adapt the LLM to the real-world environments and PIORS settings. We evaluate the effectiveness of PIORS and SFMSS through automatic and human assessments involving 15 users and 15 clinical experts. The results demonstrate that PIORS-Nurse outperforms all baselines, including the current state-of-the-art model GPT-4o, and aligns with human preferences and clinical needs. 

The overall framework of PIORS is shown below.
![image](https://github.com/user-attachments/assets/41549ccf-e87e-4d81-8b4c-145d33d5dd1d)

## Citation
```
@misc{bao2024piors,
    title={PIORS: Personalized Intelligent Outpatient Reception based on Large Language Model with Multi-Agents Medical Scenario Simulation},
    author={Zhijie Bao and Qingyun Liu and Ying Guo and Zhengqiang Ye and Jun Shen and Shirong Xie and Jiajie Peng and Xuanjing Huang and Zhongyu Wei},
    year={2024},
    eprint={2411.13902},
    archivePrefix={arXiv},
    primaryClass={cs.CL}
}
```
