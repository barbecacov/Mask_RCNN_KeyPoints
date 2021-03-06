# Author : Hellcat
# Time   : 2018/12/6

"""
import os
os.environ["CUDA_VISIBLE_DEVICES"]="-1"

import numpy as np
np.set_printoptions(threshold=np.inf)

import tensorflow as tf
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)
"""

import os
import numpy as np
import pandas as pd
from PIL import Image

import utils as utils
import model as modellib
from config import Config

class_names_ = ['neckline_left', 'neckline_right', 'center_front', 'shoulder_left',
                'shoulder_right', 'armpit_left', 'armpit_right', 'waistline_left',
                'waistline_right', 'cuff_left_in', 'cuff_left_out', 'cuff_right_in',
                'cuff_right_out', 'top_hem_left', 'top_hem_right', 'waistband_left',
                'waistband_right', 'hemline_left', 'hemline_right', 'crotch',
                'bottom_left_in', 'bottom_left_out', 'bottom_right_in', 'bottom_right_out']

blouse_index = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14]  # NUM_KEYPOINTS=13
skirt_index = [15, 16, 17, 18]  # NUM_KEYPOINTS=4
outwear_index = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]  # NUM_KEYPOINTS=14
dress_index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 17, 18]  # NUM_KEYPOINTS=15
trousers_index = [15, 16, 19, 20, 21, 22, 23]  # NUM_KEYPOINTS=7

all_index = {'blouse': blouse_index,
             'skirt': skirt_index,
             'outwear': outwear_index,
             'dress': dress_index,
             'trousers': trousers_index}

fi_class_names = ['blouse']
index = all_index[fi_class_names[0]]

fi_class_names_ = []

for i in index:
    fi_class_names_.append(class_names_[i])
print(fi_class_names_)


class FIConfig(Config):
    """
    Configuration for training on the toy shapes dataset.
    Derives from the base Config class and overrides values specific
    to the toy shapes dataset.
    """

    IMAGE_CATEGORY = fi_class_names[0]
    # Give the configuration a recognizable name
    NAME = "FI"

    # Train on 1 GPU and 8 images per GPU. We can put multiple images on each
    # GPU because the images are small. Batch size is 8 (GPUs * images/GPU).
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    NUM_KEYPOINTS = len(all_index[fi_class_names[0]])  # 更改当前训练关键点数目
    KEYPOINT_MASK_SHAPE = [56, 56]
    # Number of classes (including background)
    NUM_CLASSES = 1 + 1

    RPN_TRAIN_ANCHORS_PER_IMAGE = 150
    VALIDATION_STPES = 100
    STEPS_PER_EPOCH = 1000
    MINI_MASK_SHAPE = (56, 56)
    KEYPOINT_MASK_POOL_SIZE = 7

    # Pooled ROIs
    POOL_SIZE = 7
    MASK_POOL_SIZE = 14
    MASK_SHAPE = [28, 28]
    WEIGHT_LOSS = True
    KEYPOINT_THRESHOLD = 0.005
    # Maximum number of ground truth instances to use in one image


config = FIConfig()


def pic_height_width(filepath):
    fp = open(filepath, 'rb')
    im = Image.open(fp)
    fp.close()
    x, y = im.size
    if (im.mode == 'RGB'):
        return x, y
    else:
        return False, False


class FIDataset(utils.Dataset):
    """Generates the shapes synthetic dataset. The dataset consists of simple
    shapes (triangles, squares, circles) placed randomly on a blank surface.
    The images are generated on the fly. No file access required.
    """

    def load_FI(self, category='train'):
        """Generate the requested number of synthetic images.
        count: number of images to generate.
        height, width: the size of the generated images.
        """

        if category == 'train':
            annotations = pd.concat([pd.read_csv('../keypoint_data/train1.csv'),
                                     pd.read_csv('../keypoint_data/train2.csv')],
                                    axis=0,
                                    ignore_index=True  # 忽略索引表示不会直接拼接索引，会重新计算行数索引
                                    )
            annotations = annotations[annotations.image_category.isin(['blouse'])]
            self.pd = annotations

        # Add classes
        self.add_class(source="FI", class_id=1, class_name='blouse')

        # Add images
        for i in range(annotations.shape[0]):
            annotation = annotations.iloc[i]
            img_path = os.path.join("../keypoint_data", annotation.image_id)
            keypoints = np.array([p.split('_')
                                  for p in annotations.iloc[i][2:]], dtype=int)[all_index['blouse'], :]
            keypoints[:, -1] += 1
            self.add_image(source="FI",
                           image_id=i,
                           path=img_path,
                           annotations=keypoints)

    def load_keypoints(self, image_id, with_mask=False):
        """
        Returns:
        key_points: num_keypoints coordinates and visibility (x,y,v)  [num_person,num_keypoints,3] of num_person
        masks: A bool array of shape [height, width, instance count] with
            one mask per instance.
        class_ids: a 1D array of class IDs of the instance masks, here is always equal to [num_person, 1]
        """
        key_points = np.expand_dims(self.image_info[image_id]["annotations"], 0)  # 已知图中仅有一个对象
        class_ids = np.array([1])

        if with_mask:
            annotations = self.image_info[image_id]["annotations"]
            w, h = pic_height_width(self.image_info[image_id]["path"])
            mask = np.zeros([w, h], dtype=int)
            mask[annotations[:, 1], annotations[:, 0]] = 1
            return key_points.copy(), np.expand_dims(mask, -1), class_ids
        return key_points.copy(), None, class_ids


dataset = FIDataset()
dataset.load_FI()
dataset.prepare()
original_image, image_meta, gt_class_id, gt_bbox, gt_keypoint = \
    modellib.load_image_gt_keypoints(dataset, FIConfig, 0)

# import visualize
# from model import log
#
# log("original_image", original_image)
# log("image_meta", image_meta)
# log("gt_class_id", gt_class_id)
# log("gt_bbox", gt_bbox)
# log("gt_keypoint", gt_keypoint)
#
# visualize.display_keypoints(original_image,gt_bbox,gt_keypoint,gt_class_id,dataset.class_names)

data_tra = FIDataset()
data_tra.load_FI()
data_tra.prepare()

data_val = FIDataset()
data_val.load_FI()
data_val.prepare()
model = modellib.MaskRCNN(mode='training', config=config, model_dir='./')
model.load_weights('./mask_rcnn_coco.h5', by_name=True,
                   exclude=["mrcnn_class_logits", "mrcnn_bbox_fc", "mrcnn_bbox", "mrcnn_mask"])
model.train(data_tra, data_val,
            learning_rate=config.LEARNING_RATE / 10,
            epochs=400, layers='heads')

