/**
 * router.hpp
 *
 * for Vivado HLS
 */

#ifndef __ROUTER_HPP__
#define __ROUTER_HPP__

#ifdef SOFTWARE
#include "ap_int.h"
#else
#include <ap_int.h>
#endif

// #define DEBUG_PRINT  // ���낢��\������
#define USE_ASTAR    // A* �T�����g��
#define USE_MOD_CALC // �^�[�Q�b�g���C���̑I���ɏ�]���Z��p����

using namespace std;


// �e��ݒ�l
#define MAX_WIDTH   72      // X, Y �̍ő�l (7�r�b�g�Ŏ��܂�)
#define BITWIDTH_XY 13
#define BITMASK_XY  65528   // 1111 1111 1111 1000
#define MAX_LAYER   8       // Z �̍ő�l (3�r�b�g)
#define BITWIDTH_Z  3
#define BITMASK_Z   7       // 0000 0000 0000 0111

#define MAX_CELLS  41472    // �Z���̑��� =72*72*8 (16�r�b�g�Ŏ��܂�)
// #define MAX_CELLS  200000
#define MAX_LINES  128      // ���C�����̍ő�l (7�r�b�g)
#define MAX_PATH   256      // 1�̃��C�����Ή�����Z�����̍ő�l (8�r�b�g)
#define MAX_PQ     4096     // �T�����̃v���C�I���e�B�E�L���[�̍ő�T�C�Y (12�r�b�g) ����Ȃ������H

#define PQ_PRIORITY_WIDTH 16
#define PQ_PRIORITY_MASK  65535       // 0000 0000 0000 0000 1111 1111 1111 1111
#define PQ_DATA_WIDTH     16
#define PQ_DATA_MASK      4294901760  // 1111 1111 1111 1111 0000 0000 0000 0000

#define MAX_WEIGHT 255      // �d�݂̍ő�l (8�r�b�g�Ŏ��܂�)
#define BOARDSTR_SIZE 41472 // �{�[�h�X�g�����O�̍ő啶���� (�Z���� 72*72*8 ����Ηǂ�)
// #define BOARDSTR_SIZE 200000

void lfsr_random_init(ap_uint<32> seed);
ap_uint<32> lfsr_random();
//ap_uint<32> lfsr_random_uint32(ap_uint<32> a, ap_uint<32> b);
//ap_uint<32> lfsr_random_uint32_0(ap_uint<32> b);

ap_uint<8> new_weight(ap_uint<16> x);
bool pynqrouter(char boardstr[BOARDSTR_SIZE], ap_uint<32> seed, ap_int<32> *status,string filename_path);

#ifdef USE_ASTAR
ap_uint<7> abs_uint7(ap_uint<7> a, ap_uint<7> b);
ap_uint<3> abs_uint3(ap_uint<3> a, ap_uint<3> b);
#endif

void search(ap_uint<8> *path_size, ap_uint<16> path[MAX_PATH], ap_uint<16> start, ap_uint<16> goal, ap_uint<8> w[MAX_WEIGHT]);
void pq_push(ap_uint<16> priority, ap_uint<16> data, ap_uint<12> *pq_len, ap_uint<32> pq_nodes[MAX_PQ]);
void pq_pop(ap_uint<16> *ret_priority, ap_uint<16> *ret_data, ap_uint<12> *pq_len, ap_uint<32> pq_nodes[MAX_PQ]);

#endif /* __ROUTER_HPP__ */
