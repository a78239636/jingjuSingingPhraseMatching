import os,sys
import json

currentPath = os.path.dirname(__file__)
parentPath = os.path.join(currentPath, '..')
sys.path.append(parentPath)

from scoreManip import retrieveSylInfo
from general.phonemeMap import *
from general.pinyinMap import *
import numpy as np
from scipy.linalg import block_diag

TRANS_PROB_SELF = 0.9
TRANS_PROB_NEXT = 1-TRANS_PROB_SELF

with open(os.path.join(currentPath,'dict_centroid_dur.json'),'r') as openfile:
    dict_centroid_dur = json.load(openfile)

def singleTransMatBuild(dict_score_info):
    '''
    build the transition matrix for a single path
    :param dict_score_info:
    :return:
    '''
    syl_finals,syl_durations,_ = retrieveSylInfo(dict_score_info)
    # print syl_finals,syl_durations

    # collect phone states and phone durations
    state_pho = []
    centroid_pho_durs = []
    for ii,sf in enumerate(syl_finals):
        pho_final = dic_final_2_sampa[sf]

        centroid_pho_durs_syl = []
        for pho in pho_final:
            pho_map = dic_pho_map[pho]
            if pho_map == u'H':
                pho_map = u'y'
            elif pho_map == u'9':
                pho_map = u'S'
            elif pho_map == u'yn':
                pho_map = u'in'
            state_pho.append(pho_map)

            # phoneme duration
            centroid_pho_durs_syl.append(dict_centroid_dur[pho_map])

        # normalize the phoneme durations in a syllable
        centroid_pho_durs_syl = np.array(centroid_pho_durs_syl)/np.sum(centroid_pho_durs_syl)

        # make the sum of the phoneme durations for a syllable equals to the syllable length
        centroid_pho_durs_syl *= syl_durations[ii]

        # print pho_final, syl_durations[ii], sum(centroid_pho_durs_syl), centroid_pho_durs_syl

        centroid_pho_durs += centroid_pho_durs_syl.tolist()

    # transition matrix
    num_state = len(state_pho)
    mat_trans = np.zeros((num_state,num_state))
    for ii in range(num_state-1):
        mat_trans[ii][ii] = TRANS_PROB_SELF
        mat_trans[ii][ii+1] = TRANS_PROB_NEXT
    mat_trans[-1][-1] = 1.0
    return mat_trans,state_pho,centroid_pho_durs

def multiTransMats(dict_score_infos):
    '''
    build multi transition matrix
    :param dict_score_infos:
    :return:
    '''
    phrases = []
    lyrics = []
    mats_trans = []
    states_pho = []
    list_centroid_pho_durs = []
    for key in dict_score_infos:
        mat_trans,state_pho,centroid_pho_durs = singleTransMatBuild(dict_score_infos[key])
        phrases.append(key)
        lyrics.append(dict_score_infos[key]['lyrics'])
        mats_trans.append(mat_trans)
        states_pho.append(state_pho)
        list_centroid_pho_durs.append(centroid_pho_durs)
    return phrases,lyrics,mats_trans,states_pho,list_centroid_pho_durs

def combineTransMats(mats_trans,states_pho):
    '''
    combine multi transition matrix into one matrix
    :param mats_trans:
    :param states_pho:
    :return:
    '''
    mat_trans_comb = block_diag(*mats_trans)
    state_pho_comb = sum(states_pho, [])
    index_start = [0]
    index_end = [mats_trans[0].shape[0]-1]
    for ii in range(1,len(mats_trans)):
        index_start.append(index_end[-1]+1)
        index_end.append(index_end[-1]+mats_trans[ii].shape[0])
    return mat_trans_comb,state_pho_comb,index_start,index_end

def makeNet(dict_scores):

    phrases,lyrics,mats_trans,states_pho,list_centroid_pho_durs = multiTransMats(dict_scores)
    mat_trans_comb,state_pho_comb,index_start,index_end = combineTransMats(mats_trans,states_pho)

    return phrases,lyrics,mat_trans_comb,state_pho_comb,index_start,index_end,list_centroid_pho_durs

# if __name__=='__main__':
    # phrases,mat_trans_comb,state_pho_comb,index_start,index_end = makeNet()
    #
    # dict_net = {'phrases':phrases,
    #                'mat_trans_comb':mat_trans_comb,
    #                'state_pho_comb':state_pho_comb,
    #                'index_start':index_start,
    #                'index_end':index_end}
    #
    # output = open('dict_net.pkl', 'wb')
    # pickle.dump(dict_net, output)
    # output.close()

    # print index_start
    # print index_end
    # print len(state_pho_comb)