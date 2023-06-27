/**
 * router.cpp
 *
 * for Vivado HLS
 */

#ifdef SOFTWARE
#include "ap_int.h"
#else
#include <ap_int.h>
#endif

#include "./router.hpp"
#include <iostream>
#include <string>
#include <fstream>

// ================================ //
// LFST
// ================================ //

// �Q�l https://highlevel-synthesis.com/2017/02/10/lfsr-in-hls/
static ap_uint<32> lfsr;

void lfsr_random_init(ap_uint<32> seed) {
#pragma HLS INLINE
    lfsr = seed;
}

ap_uint<32> lfsr_random() {
#pragma HLS INLINE
    bool b_32 = lfsr.get_bit(32-32);
    bool b_22 = lfsr.get_bit(32-22);
    bool b_2 = lfsr.get_bit(32-2);
    bool b_1 = lfsr.get_bit(32-1);
    bool new_bit = b_32 ^ b_22 ^ b_2 ^ b_1;
    lfsr = lfsr >> 1;
    lfsr.set_bit(31, new_bit);
    
    return lfsr.to_uint();
}

// A����B�͈̔� (A��B���܂�) �̐����̗������~�����Ƃ�
// �Q�l http://www.sat.t.u-tokyo.ac.jp/~omi/random_variables_generation.html
/*ap_uint<32> lfsr_random_uint32(ap_uint<32> a, ap_uint<32> b) {
#pragma HLS INLINE
    return lfsr_random() % (b - a + 1) + a;
}*/

// 0����B�͈̔� (A��B���܂�) �̐����̗������~�����Ƃ�
// �Q�l http://www.sat.t.u-tokyo.ac.jp/~omi/random_variables_generation.html
/*ap_uint<32> lfsr_random_uint32_0(ap_uint<32> b) {
#pragma HLS INLINE
    return lfsr_random() % (b + 1);
}*/


// ================================ //
// ���C�����W���[��
// ================================ //

// �d�݂̍X�V
// TODO ����
// min_uint8(r, MAX_WEIGHT) �Ɠ���
ap_uint<8> new_weight(ap_uint<16> x) {
#pragma HLS INLINE
#if 1
    // ����8�r�b�g (�ő� 255) �𔲂��o���āA1/8 �������čő� 31 (32) �ɂ���
    ap_uint<8> y = x & 255;
    return (ap_uint<8>)(y / 8 + 1);
#endif
#if 0
    // ����10�r�b�g (�ő� 1023) �𔲂��o���āA1/32 �������čő� 31 (32) �ɂ���
    ap_uint<10> y = x & 1023;
    return (ap_uint<8>)(y / 32 + 1);
#endif
#if 0
    ap_uint<8> y = x / 8;
    if (y < (ap_uint<16>)MAX_WEIGHT) { return y; }
    else { return MAX_WEIGHT; }
#endif
}

// �{�[�h�Ɋւ���ϐ�
static ap_uint<7> size_x;       // �{�[�h�� X �T�C�Y
static ap_uint<7> size_y;       // �{�[�h�� Y �T�C�Y
static ap_uint<4> size_z;       // �{�[�h�� Z �T�C�Y

static ap_uint<7> line_num = 0; // ���C���̑���

// �O���[�o���ϐ��Œ�`����
#ifdef GLOBALVARS
    ap_uint<16> starts[MAX_LINES];          // ���C���̃X�^�[�g���X�g
    ap_uint<16> goals[MAX_LINES];           // ���C���̃S�[�����X�g

    ap_uint<8> weights[MAX_CELLS];          // �Z���̏d��

    ap_uint<8> paths_size[MAX_LINES];       // ���C�����Ή�����Z��ID�̃T�C�Y
    ap_uint<16> paths[MAX_LINES][MAX_PATH]; // ���C�����Ή�����Z��ID�̏W�� (�X�^�[�g�ƃS�[���͏���)
    bool adjacents[MAX_LINES];              // �X�^�[�g�ƃS�[�����אڂ��Ă��郉�C��
#endif

bool pynqrouter(char boardstr[BOARDSTR_SIZE], ap_uint<32> seed, ap_int<32> *status, string filename_path) {
#pragma HLS INTERFACE s_axilite port=boardstr bundle=AXI4LS
#pragma HLS INTERFACE s_axilite port=seed bundle=AXI4LS
#pragma HLS INTERFACE s_axilite port=status bundle=AXI4LS
#pragma HLS INTERFACE s_axilite port=return bundle=AXI4LS

    *status = -1;

// �O���[�o���ϐ��ł͒�`���Ȃ�
#ifndef GLOBALVARS
    ap_uint<16> starts[MAX_LINES];          // ���C���̃X�^�[�g���X�g
#pragma HLS ARRAY_PARTITION variable=starts complete dim=1
    ap_uint<16> goals[MAX_LINES];           // ���C���̃S�[�����X�g
#pragma HLS ARRAY_PARTITION variable=goals complete dim=1

    ap_uint<8> weights[MAX_CELLS];          // �Z���̏d��
//#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=8 dim=1 partition
// Note: weights �͗l�X�ȏ��ԂŃA�N�Z�X����邩��p�[�e�B�V�������Ă��S�R���ʂȂ�

    ap_uint<8> paths_size[MAX_LINES];       // ���C�����Ή�����Z��ID�̃T�C�Y
//#pragma HLS ARRAY_PARTITION variable=paths_size complete dim=1
    ap_uint<16> paths[MAX_LINES][MAX_PATH]; // ���C�����Ή�����Z��ID�̏W�� (�X�^�[�g�ƃS�[���͏���)
//#pragma HLS ARRAY_PARTITION variable=paths cyclic factor=16 dim=2 partition
    bool adjacents[MAX_LINES];              // �X�^�[�g�ƃS�[�����אڂ��Ă��郉�C��
//#pragma HLS ARRAY_PARTITION variable=adjacents complete dim=1
    ap_uint<16> core[MAX_CELLS]; 

#endif

    // ================================
    // ������ BEGIN
    // ================================

    // ���[�v�J�E���^��1�r�b�g�]���ɗp�ӂ��Ȃ��ƏI������ł��Ȃ�
    INIT_ADJACENTS:
    for (ap_uint<8> i = 0; i < (ap_uint<8>)(MAX_LINES); i++) {
        adjacents[i] = false;
    }

    INIT_WEIGHTS:
    for (ap_uint<16> i = 0; i < (ap_uint<16>)(MAX_CELLS); i++) {
//#pragma HLS PIPELINE
//#pragma HLS UNROLL factor=8
        weights[i] = 1;
    }
    for (ap_uint<16> i = 0; i < (ap_uint<16>)(MAX_CELLS); i++) {
//#pragma HLS PIPELINE
//#pragma HLS UNROLL factor=8
        core[i] = 0;
    }

    // �{�[�h�X�g�����O�̉���

    size_x = (boardstr[1] - '0') * 10 + (boardstr[2] - '0');
    // size_x = (boardstr[1] - '0') * 100 + (boardstr[2] - '0') * 10 + (boardstr[3] - '0');
    size_y = (boardstr[4] - '0') * 10 + (boardstr[5] - '0');
    // size_y = (boardstr[5] - '0') * 100 + (boardstr[6] - '0') * 10 + (boardstr[7] - '0');
    size_z = (boardstr[7] - '0');
    // size_z = (boardstr[9] - '0');

    INIT_BOARDS:
    for (ap_uint<16> idx = 8; idx < BOARDSTR_SIZE; idx+=11) {
//#pragma HLS LOOP_TRIPCOUNT min=100 max=32768 avg=1000

        // �I�[ (null) ����
        if (boardstr[idx] == 0) {
            break;
        }

        if (boardstr[idx] == 'C') {
            break;
        }

        ap_uint<7> s_x = (boardstr[idx+1] - '0') * 10 + (boardstr[idx+2] - '0');
        ap_uint<7> s_y = (boardstr[idx+3] - '0') * 10 + (boardstr[idx+4] - '0');
        ap_uint<3> s_z = (boardstr[idx+5] - '0') - 1;
        ap_uint<7> g_x = (boardstr[idx+6] - '0') * 10 + (boardstr[idx+7] - '0');
        ap_uint<7> g_y = (boardstr[idx+8] - '0') * 10 + (boardstr[idx+9] - '0');
        ap_uint<3> g_z = (boardstr[idx+10] - '0') - 1;
        //cout << "L " << line_num << ": (" << s_x << ", " << s_y << ", " << s_z << ") "
        //                             "(" << g_x << ", " << g_y << ", " << g_z << ")" << endl;

        // �X�^�[�g�ƃS�[��
        ap_uint<16> start_id = (((ap_uint<16>)s_x * MAX_WIDTH + (ap_uint<16>)s_y) << BITWIDTH_Z) | (ap_uint<16>)s_z;
        ap_uint<16> goal_id  = (((ap_uint<16>)g_x * MAX_WIDTH + (ap_uint<16>)g_y) << BITWIDTH_Z) | (ap_uint<16>)g_z;
        starts[line_num] = start_id;
        goals[line_num]  = goal_id;

        // ������ԂŐ������אڂ��Ă��邩���f
        ap_int<8> dx = (ap_int<8>)g_x - (ap_int<8>)s_x; // �ŏ�-71 �ő�71 (-> �����t��8�r�b�g)
        ap_int<8> dy = (ap_int<8>)g_y - (ap_int<8>)s_y; // �ŏ�-71 �ő�71 (-> �����t��8�r�b�g)
        ap_int<4> dz = (ap_int<4>)g_z - (ap_int<4>)s_z; // �ŏ�-7  �ő�7  (-> �����t��4�r�b�g)
        if ((dx == 0 && dy == 0 && (dz == 1 || dz == -1)) || (dx == 0 && (dy == 1 || dy == -1) && dz == 0) || ((dx == 1 || dx == -1) && dy == 0 && dz == 0)) {
            adjacents[line_num] = true;
            paths_size[line_num] = 0;
        } else {
            adjacents[line_num] = false;
        }

        paths_size[line_num] = 0;
        weights[start_id] = MAX_WEIGHT;
        weights[goal_id]  = MAX_WEIGHT;

        line_num++;
    }
    for (ap_uint<16> idx = 8; idx < BOARDSTR_SIZE; idx+=11) {
//#pragma HLS LOOP_TRIPCOUNT min=100 max=32768 avg=1000

        // �I�[ (null) ����
        if (boardstr[idx] == 0) {
            break;
        }

        ap_uint<7> s_x = (boardstr[idx+1] - '0') * 10 + (boardstr[idx+2] - '0');
        ap_uint<7> s_y = (boardstr[idx+3] - '0') * 10 + (boardstr[idx+4] - '0');
        ap_uint<3> s_z = (boardstr[idx+5] - '0') - 1;
        ap_uint<7> g_x = (boardstr[idx+6] - '0') * 10 + (boardstr[idx+7] - '0');
        ap_uint<7> g_y = (boardstr[idx+8] - '0') * 10 + (boardstr[idx+9] - '0');
        ap_uint<3> g_z = (boardstr[idx+10] - '0') - 1;
        //cout << "L " << line_num << ": (" << s_x << ", " << s_y << ", " << s_z << ") "
        //                             "(" << g_x << ", " << g_y << ", " << g_z << ")" << endl;

        // �X�^�[�g�ƃS�[��
        ap_uint<16> start_id = (((ap_uint<16>)s_x * MAX_WIDTH + (ap_uint<16>)s_y) << BITWIDTH_Z) | (ap_uint<16>)s_z;
        ap_uint<16> goal_id  = (((ap_uint<16>)g_x * MAX_WIDTH + (ap_uint<16>)g_y) << BITWIDTH_Z) | (ap_uint<16>)g_z;

        // change_point
        if (boardstr[idx] == 'C') {
            // printf("=====core======\n");
            weights[start_id] = MAX_WEIGHT;
            core[start_id] = 1;
        }
    }


    // cout << size_x << " " << size_y << " " << size_z << endl;
    // cout << line_num << endl;

    // �����̏�����
    lfsr_random_init(seed);

    // TODO
    // ���ׂẴ��C�����אڂ��Ă���\���o���I���ɂ���

    // ================================
    // ������ END
    // ================================

    // ================================
    // ���[�e�B���O BEGIN
    // ================================

    // [Step 1] �������[�e�B���O
    //cout << "Initial Routing" << endl;
    FIRST_ROUTING:
    for (ap_uint<8> i = 0; i < (ap_uint<8>)(line_num); i++) {
#pragma HLS LOOP_TRIPCOUNT min=2 max=127 avg=50
//#pragma HLS PIPELINE
//#pragma HLS UNROLL factor=2

        // �������אڂ���ꍇ�X�L�b�v�A�����łȂ��ꍇ�͎��s
        if (adjacents[i] == false) {

            // cout << "LINE #" << (int)(i + 1) << endl;
            // cout << starts[i] << "," << goals[i] << endl;
            search(&(paths_size[i]), paths[i], starts[i], goals[i], weights);

        }
    }

    ap_uint<1> overlap_checks[MAX_CELLS];
#pragma HLS ARRAY_PARTITION variable=overlap_checks cyclic factor=16 dim=1 partition
    bool has_overlap = false;

#ifndef USE_MOD_CALC
    // line_num_2: line_num �ȏ�ōŏ���2�ׂ̂��搔
    ap_uint<8> line_num_2;
    CALC_LINE_NUM_2:
    for (line_num_2 = 1; line_num_2 < (ap_uint<8>)line_num; line_num_2 *= 2) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=8 avg=4
        ;
    }
    cout << "line_num: " << line_num << endl;
    cout << "line_num_2: " << line_num_2 << endl;
#endif

    ap_uint<8> last_target = 255;

    // [Step 2] Rip-up �ă��[�e�B���O
    ROUTING:
    for (ap_uint<16> round = 1; round <= 32768 /* = (2048 * 16) */; round++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=4000 avg=50

#ifdef DEBUG_PRINT
        //cout << "ITERATION " << round;
#endif

        // �Ώۃ��C����I��
#ifdef USE_MOD_CALC
        // (1) ��]���Z��p������@
        // cout << line_num << endl;
        ap_uint<8> target = lfsr_random() % line_num; // i.e., lfsr_random_uint32(0, line_num - 1);
        // srand((unsigned int)time(NULL));
        // ap_uint<8> target = rand() % line_num;

        // cout << "=======" << endl;
        // cout << target << "," << last_target <<  endl;

#else
        // (2) ��]���Z��p���Ȃ����@
        ap_uint<8> target = lfsr_random() & (line_num_2 - 1);
        if (line_num <= target) {
            //cout << endl;
            continue;
        }
#endif

        // �������אڂ���ꍇ�X�L�b�v�A�����łȂ��ꍇ�͎��s
        if (adjacents[target] == true) {
            
            continue;
        }

        // ���O�̃C�e���[�V���� (���E���h) �Ɠ����Ώۃ��C���������烋�[�e�B���O�X�L�b�v����
        if (target == last_target) {
            
            //cout << endl;
            continue;
        }
        last_target = target;

        // (1) �����͂������C���̏d�݂����Z�b�g
        ROUTING_RESET:
        for (ap_uint<9> j = 0; j < (ap_uint<9>)(paths_size[target]); j++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=255 avg=50
            weights[paths[target][j]] = 1;
        }
        // �Ώۃ��C���̃X�^�[�g�̏d�݂���U���Z�b�g ���Ƃ� (*) �Ŗ߂�
        weights[starts[target]] = 1;

        // (2) �d�݂��X�V
        ap_uint<8> current_round_weight = new_weight(round);
        //cout << "  weight " << current_round_weight << endl;
        ROUTING_UPDATE:
        for (ap_uint<8> i = 0; i < (ap_uint<8>)(line_num); i++) {
#pragma HLS LOOP_TRIPCOUNT min=2 max=127 avg=50

            // �������אڂ���ꍇ�X�L�b�v�A�����łȂ��ꍇ�͎��s
            if (adjacents[i] == false && i != target) {
                ROUTING_UPDATE_PATH:
                for (ap_uint<9> j = 0; j < (ap_uint<9>)(paths_size[i]); j++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=255 avg=50
                    weights[paths[i][j]] = current_round_weight;
                }
            }
        }

        // �o�H�T��
        //cout << "=============" << endl;
        //cout << "LINE #" << (int)(target + 1) << endl;

        search(&(paths_size[target]), paths[target], starts[target], goals[target], weights);

        // (*) �Ώۃ��C���̃X�^�[�g�̏d�݂�߂�
        weights[starts[target]] = MAX_WEIGHT;

        // ���[�e�B���O��
        // �I�[�o�[���b�v�̃`�F�b�N
        has_overlap = false;
        OVERLAP_RESET:
        for (ap_uint<16> i = 0; i < (ap_uint<16>)(MAX_CELLS); i++) {
#pragma HLS UNROLL factor=16
            overlap_checks[i] = core[i];
        }


        OVERLAP_CHECK:
        for (ap_uint<8> i = 0; i < (ap_uint<8>)(line_num); i++) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS LOOP_TRIPCOUNT min=2 max=127 avg=50
            overlap_checks[starts[i]] = 1;
            overlap_checks[goals[i]] = 1;

            // �������אڂ���ꍇ�X�L�b�v�A�����łȂ��ꍇ�͎��s
            //if (adjacents[i] == false) {

            OVERLAP_CHECK_PATH:
            // cout << "overlap_check" << endl;
            // cout << "line_num = " << i << endl;
            for (ap_uint<9> j = 0; j < (ap_uint<9>)(paths_size[i]); j++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=255 avg=50
//#pragma HLS PIPELINE rewind II=33
#pragma HLS PIPELINE II=17
#pragma HLS UNROLL factor=8
                ap_uint<16> cell_id = paths[i][j];
                // cout << overlap_checks[cell_id] << endl;
                if (overlap_checks[cell_id] == 1) {
                    has_overlap = true;
                    
                    break;
                }
                overlap_checks[cell_id] = 1;
            }
            //}
        }
        // �I�[�o�[���b�v�Ȃ���ΒT���I��
        if (has_overlap == false) {
            break;
        }

    }

    // �𓱏o�ł��Ȃ������ꍇ
    if (has_overlap == true) {
        *status = 1;
        return false;
    }

    // ================================
    // ���[�e�B���O END
    // ================================

    // ================================
    // �𐶐� BEGIN
    // ================================

    // ��
    OUTPUT_INIT:
    for (ap_uint<16> i = 0; i < (ap_uint<16>)(MAX_CELLS); i++) {
        boardstr[i] = 0;
    }
    // ���C��
    // ���̃\���o�ł̃��C��ID��+1���ĕ\������
    // �Ȃ��Ȃ�󔒂� 0 �ŕ\�����Ƃɂ��邩�烉�C��ID�� 1 �ȏ�ɂ�����
    OUTPUT_LINE:
    ofstream writing_file;
    writing_file.open(filename_path.c_str(),ios::out);
    // cout << "writing" << filename_path << "..." << endl;

    for (ap_uint<8> i = 0; i < (ap_uint<8>)(line_num); i++) {
#pragma HLS LOOP_TRIPCOUNT min=2 max=127 avg=50
        boardstr[starts[i]] = (i + 1);
        boardstr[goals[i]]  = (i + 1);
        writing_file << endl << "path" << i+1 << endl;
        int g_xy = goals[i] >> BITWIDTH_Z;
        int g_x = g_xy / MAX_WIDTH;
        int g_y = g_xy % MAX_WIDTH;
        int g_z = goals[i] & BITMASK_Z;
        writing_file << "(" << g_x << "," << g_y << "," << g_z << ")" << endl;
        
        OUTPUT_LINE_PATH:
        for (ap_uint<9> j = 0; j < (ap_uint<9>)(paths_size[i]); j++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=255 avg=50
            boardstr[paths[i][j]] = (i + 1);
            int t_xy = paths[i][j] >> BITWIDTH_Z;
            int t_x = t_xy / MAX_WIDTH;
            int t_y = t_xy % MAX_WIDTH;
            int t_z = paths[i][j] & BITMASK_Z;

            writing_file << "(" << t_x << "," << t_y << "," << t_z << ")" << endl;
        }
        int s_xy = starts[i] >> BITWIDTH_Z;
        int s_x = s_xy / MAX_WIDTH;
        int s_y = s_xy % MAX_WIDTH;
        int s_z = starts[i] & BITMASK_Z;
        writing_file << "(" << s_x << "," << s_y << "," << s_z << ")" << endl;

    }
    // writing_file << endl;
    // cout << "finish!" << endl;

    // ================================
    // �𐶐� END
    // ================================

    *status = 0;
    return true;
}


// ================================ //
// �T��
// ================================ //

#ifdef USE_ASTAR
// A* �q���[���X�e�B�b�N�p
// �ő�71 �ŏ�0
ap_uint<7> abs_uint7(ap_uint<7> a, ap_uint<7> b) {
#pragma HLS INLINE
    if (a < b) { return b - a; }
    else  { return a - b; }
}
// �ő�7 �ŏ�0
ap_uint<3> abs_uint3(ap_uint<3> a, ap_uint<3> b) {
#pragma HLS INLINE
    if (a < b) { return b - a; }
    else  { return a - b; }
}
#endif

// * Python�Ń_�C�N�X�g���A���S���Y������������ - �t�c�[���Č����Ȃ��I
//   http://lethe2211.hatenablog.com/entry/2014/12/30/011030
// * Implementation of A*
//   http://www.redblobgames.com/pathfinding/a-star/implementation.html
// ���x�[�X
void search(ap_uint<8> *path_size, ap_uint<16> path[MAX_PATH], ap_uint<16> start, ap_uint<16> goal, ap_uint<8> w[MAX_CELLS]) {
//#pragma HLS INLINE // search�֐��̓C�����C������ƒx���Ȃ邵BRAM����Ȃ��Ȃ�
//#pragma HLS FUNCTION_INSTANTIATE variable=start
//#pragma HLS FUNCTION_INSTANTIATE variable=goal

    ap_uint<16> dist[MAX_CELLS]; // �n�_����e���_�܂ł̍ŒZ�������i�[����
#pragma HLS ARRAY_PARTITION variable=dist cyclic factor=64 dim=1 partition
// Note: dist �̃p�[�e�B�V������ factor �� 128 �ɂ����BRAM������Ȃ��Ȃ�
    ap_uint<16> prev[MAX_CELLS]; // �ŒZ�o�H�ɂ�����C���̒��_�̑O�̒��_��ID���i�[����

    SEARCH_INIT_DIST:
    for (ap_uint<16> i = 0; i < MAX_CELLS; i++) {
#pragma HLS UNROLL factor=64
        dist[i] = 65535; // = (2^16 - 1)
    }

    // �v���C�I���e�B�E�L���[
    ap_uint<12> pq_len = 0;
    ap_uint<32> pq_nodes[MAX_PQ];
//#pragma HLS ARRAY_PARTITION variable=pq_nodes complete dim=1
//#pragma HLS ARRAY_PARTITION variable=pq_nodes cyclic factor=2 dim=1 partition

#ifdef DEBUG_PRINT
    // �L���[�̍ő咷���`�F�b�N�p
    ap_uint<12> max_pq_len = 0;
#endif

#ifdef USE_ASTAR
    // �S�[���̍��W
    ap_uint<13> goal_xy = (ap_uint<13>)(goal >> BITWIDTH_Z);
    ap_uint<7> goal_x = (ap_uint<7>)(goal_xy / MAX_WIDTH);
    ap_uint<7> goal_y = (ap_uint<7>)(goal_xy - goal_x * MAX_WIDTH);
    ap_uint<3> goal_z = (ap_uint<3>)(goal & BITMASK_Z);
#endif

    dist[start] = 0;
    pq_push(0, start, &pq_len, pq_nodes); // �n�_��push
#ifdef DEBUG_PRINT
    if (max_pq_len < pq_len) { max_pq_len = pq_len; }
#endif

    SEARCH_PQ:
    while (0 < pq_len) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS LOOP_TRIPCOUNT min=1 max=1000 avg=100

        ap_uint<16> prov_cost;
        ap_uint<16> src;
        pq_pop(&prov_cost, &src, &pq_len, pq_nodes);
#ifdef DEBUG_PRINT
//ap_uint<13> _src_xy = (ap_uint<13>)(src >> BITWIDTH_Z);
//ap_uint<7> _src_x = (ap_uint<7>)(_src_xy / MAX_WIDTH);
//ap_uint<7> _src_y = (ap_uint<7>)(_src_xy % MAX_WIDTH);
//ap_uint<3> _src_z = (ap_uint<3>)(src & BITMASK_Z);
//cout << "Picked up " << (int)src << " (" << (int)_src_x << "," << (int)_src_y << "," << (int)_src_z << ") prov_cost=" << (int)prov_cost << " this_cost=" << w[src] << endl;
#endif
        ap_uint<16> dist_src = dist[src];

#ifndef USE_ASTAR
        // �v���C�I���e�B�L���[�Ɋi�[����Ă���ŒZ�������C���݌v�Z�ł��Ă���ŒZ�������傫����΁Cdist�̍X�V������K�v�͂Ȃ�
        if (dist_src < prov_cost) {
            continue;
        }
#endif

        // PQ�̐擪���S�[���̏ꍇ��PQ���܂��󂶂�Ȃ��Ă��T���I��点���܂�
        if (src == goal) {
            break;
        }

        // �אڂ��鑼�̒��_�̒T��
        // (0) �R�X�g
        ap_uint<8> cost = w[src];
        // (1) �m�[�hID����3�������W���}�X�N���Ĕ����o��
        ap_uint<13> src_xy = (ap_uint<13>)(src >> BITWIDTH_Z);
        ap_uint<7> src_x = (ap_uint<7>)(src_xy / MAX_WIDTH);
        ap_uint<7> src_y = (ap_uint<7>)(src_xy - src_x * MAX_WIDTH);
        ap_uint<3> src_z = (ap_uint<3>)(src & BITMASK_Z);
        //cout << src << " " << src_x << " " << src_y << " " << src_z << endl;
        // (2) 3�������W�ŗאڂ���m�[�h (6��) �𒲂ׂ� // �蓮���[�v�W�J
/***********************************************************
        if (src_x > 0) { // x-�𒲍�
            ap_uint<16> dest = (((ap_uint<16>)(src_x-1) * MAX_WIDTH + (ap_uint<16>)(src_y)) << BITWIDTH_Z) | (ap_uint<16>)(src_z);
            ap_uint<16> dist_new = dist_src + cost;
            if (dist[dest] > dist_new) {
                dist[dest] = dist_new; // dist�̍X�V
                prev[dest] = src; // �O�̒��_���L�^
                dist_new += abs_uint7(src_x-1, goal_x) + abs_uint7(src_y, goal_y) + abs_uint3(src_z, goal_z); // A* �q���[���X�e�B�b�N
                pq_push(dist_new, dest, &pq_len, pq_nodes); // �L���[�ɐV���ȉ��̋����̏���push
            }
        }
        if (src_x < (size_x-1)) { // x+�𒲍�
            ap_uint<16> dest = (((ap_uint<16>)(src_x+1) * MAX_WIDTH + (ap_uint<16>)(src_y)) << BITWIDTH_Z) | (ap_uint<16>)(src_z);
            ap_uint<16> dist_new = dist_src + cost;
            if (dist[dest] > dist_new) {
                dist[dest] = dist_new; // dist�̍X�V
                prev[dest] = src; // �O�̒��_���L�^
                dist_new += abs_uint7(src_x+1, goal_x) + abs_uint7(src_y, goal_y) + abs_uint3(src_z, goal_z); // A* �q���[���X�e�B�b�N
                pq_push(dist_new, dest, &pq_len, pq_nodes); // �L���[�ɐV���ȉ��̋����̏���push
            }
        }
        if (src_y > 0) { // y-�𒲍�
            ap_uint<16> dest = (((ap_uint<16>)(src_x) * MAX_WIDTH + (ap_uint<16>)(src_y-1)) << BITWIDTH_Z) | (ap_uint<16>)(src_z);
            ap_uint<16> dist_new = dist_src + cost;
            if (dist[dest] > dist_new) {
                dist[dest] = dist_new; // dist�̍X�V
                prev[dest] = src; // �O�̒��_���L�^
                dist_new += abs_uint7(src_x, goal_x) + abs_uint7(src_y-1, goal_y) + abs_uint3(src_z, goal_z); // A* �q���[���X�e�B�b�N
                pq_push(dist_new, dest, &pq_len, pq_nodes); // �L���[�ɐV���ȉ��̋����̏���push
            }
        }
        if (src_y < (size_y-1)) { // y+�𒲍�
            ap_uint<16> dest = (((ap_uint<16>)(src_x) * MAX_WIDTH + (ap_uint<16>)(src_y+1)) << BITWIDTH_Z) | (ap_uint<16>)(src_z);
            ap_uint<16> dist_new = dist_src + cost;
            if (dist[dest] > dist_new) {
                dist[dest] = dist_new; // dist�̍X�V
                prev[dest] = src; // �O�̒��_���L�^
                dist_new += abs_uint7(src_x, goal_x) + abs_uint7(src_y+1, goal_y) + abs_uint3(src_z, goal_z); // A* �q���[���X�e�B�b�N
                pq_push(dist_new, dest, &pq_len, pq_nodes); // �L���[�ɐV���ȉ��̋����̏���push
            }
        }
        if (src_z > 0) { // z-�𒲍�
            ap_uint<16> dest = (((ap_uint<16>)(src_x) * MAX_WIDTH + (ap_uint<16>)(src_y)) << BITWIDTH_Z) | (ap_uint<16>)(src_z-1);
            ap_uint<16> dist_new = dist_src + cost;
            if (dist[dest] > dist_new) {
                dist[dest] = dist_new; // dist�̍X�V
                prev[dest] = src; // �O�̒��_���L�^
                dist_new += abs_uint7(src_x, goal_x) + abs_uint7(src_y, goal_y) + abs_uint3(src_z-1, goal_z); // A* �q���[���X�e�B�b�N
                pq_push(dist_new, dest, &pq_len, pq_nodes); // �L���[�ɐV���ȉ��̋����̏���push
            }
        }
        if (src_z < (size_z-1)) { // y+�𒲍�
            ap_uint<16> dest = (((ap_uint<16>)(src_x) * MAX_WIDTH + (ap_uint<16>)(src_y)) << BITWIDTH_Z) | (ap_uint<16>)(src_z+1);
            ap_uint<16> dist_new = dist_src + cost;
            if (dist[dest] > dist_new) {
                dist[dest] = dist_new; // dist�̍X�V
                prev[dest] = src; // �O�̒��_���L�^
                dist_new += abs_uint7(src_x, goal_x) + abs_uint7(src_y, goal_y) + abs_uint3(src_z+1, goal_z); // A* �q���[���X�e�B�b�N
                pq_push(dist_new, dest, &pq_len, pq_nodes); // �L���[�ɐV���ȉ��̋����̏���push
            }
        }
***********************************************************/

        SEARCH_ADJACENTS:
        for (ap_uint<3> a = 0; a < 6; a++) {
//#pragma HLS PIPELINE
//#pragma HLS UNROLL factor=2
            ap_int<8> dest_x = (ap_int<8>)src_x; // �ŏ�-1 �ő�72 (->�����t��8�r�b�g)
            ap_int<8> dest_y = (ap_int<8>)src_y; // �ŏ�-1 �ő�72 (->�����t��8�r�b�g)
            ap_int<5> dest_z = (ap_int<5>)src_z; // �ŏ�-1 �ő�8  (->�����t��5�r�b�g)
            if (a == 0) { dest_x -= 1; }
            if (a == 1) { dest_x += 1; }
            if (a == 2) { dest_y -= 1; }
            if (a == 3) { dest_y += 1; }
            if (a == 4) { dest_z -= 1; }
            if (a == 5) { dest_z += 1; }

            if (0 <= dest_x && dest_x < (ap_int<8>)size_x && 0 <= dest_y && dest_y < (ap_int<8>)size_y && 0 <= dest_z && dest_z < (ap_int<5>)size_z) {
                ap_uint<16> dest = (((ap_uint<16>)dest_x * MAX_WIDTH + (ap_uint<16>)dest_y) << BITWIDTH_Z) | (ap_uint<16>)dest_z;
                ap_uint<16> dist_new = dist_src + cost;
#ifdef DEBUG_PRINT
//cout << "  adjacent " << (int)dest << " (" << (int)dest_x << "," << (int)dest_y << "," << (int)dest_z << ") dist_new=" << (int)dist_new;
#endif
                if (dist[dest] > dist_new) {
                    dist[dest] = dist_new; // dist�̍X�V
                    prev[dest] = src; // �O�̒��_���L�^
#ifdef USE_ASTAR
                    dist_new += abs_uint7(dest_x, goal_x) + abs_uint7(dest_y, goal_y) + abs_uint3(dest_z, goal_z); // A* �q���[���X�e�B�b�N
#endif
                    pq_push(dist_new, dest, &pq_len, pq_nodes); // �L���[�ɐV���ȉ��̋����̏���push
#ifdef DEBUG_PRINT
//cout << " h=" << (int)(abs_uint7(dest_x, goal_x) + abs_uint7(dest_y, goal_y) + abs_uint3(dest_z, goal_z)) << endl;
//cout << (int)dest_x << " " << (int)goal_x << " " << (int)abs_uint7(dest_x, goal_x) << endl;
//cout << (int)dest_y << " " << (int)goal_y << " " << (int)abs_uint7(dest_y, goal_y) << endl;
//cout << (int)dest_z << " " << (int)goal_z << " " << (int)abs_uint7(dest_z, goal_z) << endl;
                    if (max_pq_len < pq_len) { max_pq_len = pq_len; }
#endif
                }
#ifdef DEBUG_PRINT
//else { cout << " -> skip pushing" << endl; }
#endif
            }
        }
    }

    // �o�H���o��
    // �S�[������X�^�[�g�ւ̏��Ԃŕ\������� (�S�[���ƃX�^�[�g�͊܂܂�Ȃ�)
    // cout << goal << "->" << endl;
    ap_uint<16> t = prev[goal];

#ifdef DEBUG_PRINT
    int dbg_start_xy = start >> BITWIDTH_Z;
    int dbg_start_x = dbg_start_xy / MAX_WIDTH;
    int dbg_start_y = dbg_start_xy % MAX_WIDTH;
    int dbg_start_z = start & BITMASK_Z;

    int dbg_goal_xy = goal >> BITWIDTH_Z;
    int dbg_goal_x = dbg_goal_xy / MAX_WIDTH;
    int dbg_goal_y = dbg_goal_xy % MAX_WIDTH;
    int dbg_goal_z = goal & BITMASK_Z;

    // cout << "(" << dbg_start_x << ", " << dbg_start_y << ", " << dbg_start_z << ") #" << start << " -> "
        //  << "(" << dbg_goal_x  << ", " << dbg_goal_y  << ", " << dbg_goal_z  << ") #" << goal << endl;
#endif

    // �o�b�N�g���b�N
    ap_uint<8> p = 0;
    SEARCH_BACKTRACK:
    while (t != start) {
        // cout << t << "->" << endl;
#pragma HLS LOOP_TRIPCOUNT min=1 max=255 avg=50
#pragma HLS PIPELINE II=2

#ifdef DEBUG_PRINT
        int t_xy = t >> BITWIDTH_Z;
        int t_x = t_xy / MAX_WIDTH;
        int t_y = t_xy % MAX_WIDTH;
        int t_z = t & BITMASK_Z;

        // cout << "(" << t_x << ", " << t_y << ", " << t_z << ")," << endl;
        // cout << "  via " << "(" << t_x << ", " << t_y << ", " << t_z << ") #" << prev[t] << " dist=" << dist[t] << endl;
#endif

        path[p] = t; // �L�^
        p++;

        t = prev[t]; // ���Ɉړ�
    }
    *path_size = p;

#ifdef DEBUG_PRINT
    // cout << "max_path_len = " << p << endl;
    // cout << "max_pq_len = " << max_pq_len << endl;
#endif

}

// �v���C�I���e�B�E�L���[ (�q�[�v�Ŏ���)
// �D��x�̍ŏ��l���q�[�v�̃��[�g�ɗ���
// �Q�l
//   * �q�[�v - Wikipedia https://ja.wikipedia.org/wiki/%E3%83%92%E3%83%BC%E3%83%97
//   * �񕪃q�[�v - Wikipedia https://ja.wikipedia.org/wiki/%E4%BA%8C%E5%88%86%E3%83%92%E3%83%BC%E3%83%97
//   * �q�[�v�̐��� - http://www.maroontress.com/Heap/
//   * Priority queue - Rosetta Code https://rosettacode.org/wiki/Priority_queue#C
// Note
// �C���f�b�N�X��0����n�܂�Ƃ� (0-origin index)
//   --> �e: (n-1)/2, ���̎q: 2n+1, �E�̎q: 2n+2
// �C���f�b�N�X��1����n�܂�Ƃ� (1-origin index)
//   --> �e: n/2, ���̎q: 2n, �E�̎q: 2n+1
// FPGA�I�ɂ͂ǂ�����x���͓��������� 1-origin �̕���LUT���\�[�X���Ȃ��čς� (�������z���0�v�f�����ʂɂȂ�)

// �m�[�h�̑}���́C�����ɒǉ����Ă���D��x�������������̈ʒu�܂Ńm�[�h���グ�Ă���
// �T���̓s����C�����D��x�ł͌ォ����ꂽ�����ɏo����������C
// ���[�v�̏I�������͑}���m�[�h�̗D��x����r�Ώۂ̗D��x�����������Ȃ����Ƃ�
void pq_push(ap_uint<16> priority, ap_uint<16> data, ap_uint<12> *pq_len, ap_uint<32> pq_nodes[MAX_PQ]) {
#pragma HLS INLINE

    (*pq_len)++;
    ap_uint<12> i = (*pq_len);      // target
    ap_uint<12> p = (*pq_len) >> 1; // i.e., (*pq_len) / 2; // �e
    PQ_PUSH_LOOP:
    while (i > 1 && (ap_uint<16>)(pq_nodes[p] & PQ_PRIORITY_MASK) >= priority) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=8 avg=4
//#pragma HLS PIPELINE
//#pragma HLS UNROLL factor=2
        pq_nodes[i] = pq_nodes[p];
        i = p;
        p = p >> 1; // i.e., p / 2; // �e
    }
    pq_nodes[i] = ((ap_uint<32>)data << 16) | (ap_uint<32>)priority;
}

// �m�[�h�̎��o���́C���[�g������Ă��邾��
// ���ɍŏ��̗D��x�����m�[�h�����[�g�Ɉړ������邽�߂ɁC
// �܂��C�����̃m�[�h�����[�g�Ɉړ�����
// �����̎q�ŗD��x��������������ɂ����Ă��� (���[�g��K�؂ȍ����܂ŉ�����)
// ������ċA�I�ɌJ��Ԃ�
void pq_pop(ap_uint<16> *ret_priority, ap_uint<16> *ret_data, ap_uint<12> *pq_len, ap_uint<32> pq_nodes[MAX_PQ]) {
#pragma HLS INLINE

    *ret_priority = (ap_uint<16>)(pq_nodes[1] & PQ_PRIORITY_MASK);
    *ret_data     = (ap_uint<16>)(pq_nodes[1] >> PQ_PRIORITY_WIDTH);

    //pq_nodes[1] = pq_nodes[*pq_len];
    ap_uint<12> i = 1; // �e�m�[�h
    //ap_uint<12> t = 1; // �����Ώۃm�[�h

    ap_uint<16> last_priority = (ap_uint<16>)(pq_nodes[*pq_len] & PQ_PRIORITY_MASK); // �����m�[�h�̗D��x

    PQ_POP_LOOP:
    while (1) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=8 avg=4
//#pragma HLS PIPELINE
//#pragma HLS UNROLL factor=2
        ap_uint<12> c1 = i << 1; // i.e., 2 * i;     // ���̎q
        ap_uint<12> c2 = c1 + 1; // i.e., 2 * i + 1; // �E�̎q
        if (c1 < *pq_len && (ap_uint<16>)(pq_nodes[c1] & PQ_PRIORITY_MASK) <= last_priority) {
            if (c2 < *pq_len && (ap_uint<16>)(pq_nodes[c2] & PQ_PRIORITY_MASK) <= (ap_uint<16>)(pq_nodes[c1] & PQ_PRIORITY_MASK)) {
                pq_nodes[i] = pq_nodes[c2];
                i = c2;
            }
            else {
                pq_nodes[i] = pq_nodes[c1];
                i = c1;
            }
        }
        else {
            if (c2 < *pq_len && (ap_uint<16>)(pq_nodes[c2] & PQ_PRIORITY_MASK) <= last_priority) {
                pq_nodes[i] = pq_nodes[c2];
                i = c2;
            }
            else {
                break;
            }
        }
    }
    pq_nodes[i] = pq_nodes[*pq_len];
    (*pq_len)--;

// For verification
    //for (int k = 1;k<(*pq_len);k++){
    //    cout << (ap_uint<16>)(pq_nodes[k] & PQ_PRIORITY_MASK) << " ";
    //}
    //cout << endl;
}
