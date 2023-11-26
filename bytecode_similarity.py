import math
import torch
from init_models import init_transformer
from pyevmasm import disassemble
from evm_cfg_builder.cfg import CFG
from scipy.spatial import distance
from data_manager import Dataset
import os
import utils
import numpy as np
from data_processor import BasicBlockProcessor, InstructionProcessor, TokenIDManager

file_path = os.path.realpath(__file__)
base_dir = os.path.dirname(file_path)
params = utils.Params(os.path.join(base_dir, "transformer_params.json"))

dataset = Dataset()


# def bytecode2opcode(bytecode):
#     # bytecode --> opcode
#     # ToDo1: Consistency of opcode generation (evm vs. pyevmasm)
#     opcode = disassemble(bytecode)
#
#     return opcode


def transform_opcode(bb, model):
    instruction_processor = InstructionProcessor('asm')
    token_id_manager = TokenIDManager(dataset.asm_vocab_path)
    for index in range(0, len(bb)):
        inst = bb[index].name
        inst = instruction_processor.normalize(inst)
        bb[index] = inst

    basic_block = " \n ".join(bb).replace("\t", " ")
    basic_block = " ".join(basic_block.split())

    token_list = ["<s>"] + basic_block.strip().split() + ["</s>"]
    ids = []
    for token in token_list:
        ids.append(token_id_manager.token2id(token))

    return model(ids)


def cross_compiler_normalization(bb):
    '''
    ToDo: cross-compiler normalization to be implemented
    1. get compiler version by metadata
    2. cross-compiler normalization (MISSING)
    Return Format: [str]
    '''
    normalized_bb = []
    return normalized_bb


def get_inter_features(bb):
    # (in-degree, out-degree)
    return bb.all_incoming_basic_blocks, bb.all_outgoing_basic_blocks


def get_embedding(bb, model):
    max_len = 256
    batch_size = params.batch_size
    pos = torch.LongTensor(list(range(1, 1 + max_len))).expand([batch_size, max_len])
    return model.encoder(bb, pos)


def key_instruction_mapping(bb):
    # ToDo: method from "Enabling clone detection for ethereum via smart contract birthmarks." is MISSING and UNCLEAR
    return bb


def bytecode_absolute_similarity(bytecode1, bytecode2):
    # load trained model
    model, _ = init_transformer()
    model.eval()

    # obtain CFG
    cfg1, cfg2 = CFG(bytecode1), CFG(bytecode2)
    bbs1, bbs2 = cfg1.basic_blocks, cfg2.basic_blocks
    eta = 0.5
    omega = 0.5  # adjust the weight of key instruction matching on semantics
    k = 0.5  # ToDo: no description in paper

    absolute_similarity_score = 0
    for bb1 in bbs1:
        if1 = get_inter_features(bb1)  # basic block inter-features
        X1 = key_instruction_mapping(bb1)  # key instruction mapping table x
        bb1 = transform_opcode(bb1, model) # transform opcode by transformer
        bb1 = cross_compiler_normalization(bb1) # cross compiler normalization
        eb1 = get_embedding(bb1, model)  # basic block embedding

        p_list = []
        for bb2 in bbs2:
            if2 = get_inter_features(bb2)  # basic block inter-features
            X2 = key_instruction_mapping(bb2)  # key instruction mapping table x
            bb2 = transform_opcode(bb2, model) # transform opcode by transformer
            bb2 = cross_compiler_normalization(bb2)  # cross compiler normalization
            eb2 = get_embedding(bb2, model)  # basic block embedding

            dis_v = distance.euclidean(eb1, eb2)    # basic block vector distance
            dis_if = distance.euclidean(if1, if2)   # basic block inter-features
            dis_x = distance.jaccard(X1, X2)        # key instruction combination mapping distance

            # The basic block distance
            bb_dis = (dis_v - omega * dis_x) / (dis_v + omega * dis_x + (1 - eta ** dis_if))

            # The probability calculated by dissimilar basic block pairs and similar basic block pairs
            p = 1 / (1 + math.e ** (-k * (bb_dis - 0.5)))

            p_list.append(p)

        max_p = max(p_list)
        absolute_similarity_score += np.log(max_p / (1 / len(bbs2)))
    return absolute_similarity_score


def bytecode_final_similarity(bytecode1, bytecode2):
    return bytecode_absolute_similarity(bytecode1, bytecode2) / \
           bytecode_absolute_similarity(bytecode2, bytecode2)
