/**
 * main.cpp
 *
 * for Vivado HLS
 */

#ifdef SOFTWARE
#include "ap_int.h"
#else
#include <ap_int.h>
#endif

#ifdef CALCTIME
#include <stdio.h>
#include <time.h>
#endif

#include "router.hpp"

#include <iostream>
#include <string>
#include <fstream>


int main(int argc, char *argv[]) {
    using namespace std;
    

    // �e�X�g�f�[�^ (������`��)
    // NL_Q00.txt
    //char boardstr[BOARDSTR_SIZE] = "X10Y05Z3L0000107041L0004107002L0102102021L0900100003";
    // NL_Q06.txt
    char boardstr[BOARDSTR_SIZE] = "X10Y18Z2L0900109002L0901105012L0902103052L0903103062L0904100102L0905106012L0906109022L0717109102L0808109112L0017209172L0401200072L0912208152L0009201092L0709209092L0901206052L0309204092L0701209072L0101201022L0011202152L0016202162";
    // NL_Q08.txt
    //char boardstr[BOARDSTR_SIZE] = "X17Y20Z2L0000103022L1603115052L0916107032L0302108012L1104111042L1002100002L0919116162L1616113182L1001115012L0500201182L1603213152L0600210022";

    // �w�肳��Ă�΃R�}���h���C�������蕶�����ǂݍ���
    if (1 < argc) {
        //�擪��X�ł͂Ȃ��Ȃ�ΕW�����͂���ǂݍ���
        if(argv[1][0]!='X')
        {
            char* c_p=fgets(boardstr, BOARDSTR_SIZE, stdin);
            int length=strlen(c_p);
            boardstr[length-1]=0;
        }
        else
        {
            strcpy(boardstr, argv[1]);
        }
    }

    // �w�肳��Ă�΃V�[�h�l��ǂݍ���
    int seed = 12345;

    // if (2 < argc) {
        //  seed = atoi(argv[2]);
    // }
    
    string filename_path = argv[3];

    int size_x = (boardstr[1] - '0') * 10 + (boardstr[2] - '0');
    int size_y = (boardstr[4] - '0') * 10 + (boardstr[5] - '0');
    int size_z = (boardstr[7] - '0');

    // cout << size_x << "," << size_y << "," << size_z << endl;

    // �\���o���s
    ap_int<32> status;
    clock_t clock_start, clock_done;
    clock_start = clock();
    bool result = pynqrouter(boardstr, seed, &status,filename_path);
    clock_done = clock();


    // filename is hikisuu 2
    string filename = argv[2];

    ofstream writing_file;
    writing_file.open(filename.c_str(),ios::out);

    // cout << "writing" << filename << "..." << endl;

    if (result) {
        writing_file << endl << "Test Passed!" << endl;
    } else {
        writing_file << endl << "Test Failed!" << endl;
    }
    writing_file << "status = " << (int)status << endl;
    writing_file << "elapsed = " << ((double)(clock_done - clock_start) / CLOCKS_PER_SEC) << endl << endl;

    // ��\��
    writing_file << "SOLUTION" << endl;
    writing_file << "========" << endl;
    
    writing_file << "SIZE " << size_x << "X" << size_y << "X" << size_z << endl;
    // cout << "SIZE " << size_x << "X" << size_y << "X" << size_z << endl;
    for (int z = 0; z < size_z; z++) {
        writing_file << "LAYER " << (z + 1) << endl;
        // cout << "LAYER " << (z + 1) << endl;
        for (int y = 0; y < size_y; y++) {
            for (int x = 0; x < size_x; x++) {
                if (x != 0) {
                    writing_file << ",";
                    // cout << ",";
                }
                int i = ((x * MAX_WIDTH + y) << BITWIDTH_Z) | z;
                //cout << setfill('0') << setw(2) << right << (unsigned int)(unsigned char)(boardstr[i]);
                writing_file << (unsigned int)(unsigned char)(boardstr[i]);
                // cout << (unsigned int)(unsigned char)(boardstr[i]);
            }
            writing_file << endl;
            // cout << endl;
        }
    }
    
    // cout << "finish" << endl;

    return 0;
}
