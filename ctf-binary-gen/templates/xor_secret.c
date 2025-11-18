#include <stdio.h>
#include <string.h>
unsigned char secret[] = "{XOR_ENC}";
void decode_and_print(){
    for(size_t i=0;i<sizeof(secret)-1;i++){
        secret[i] ^= {KEY};
    }
    printf("secret: %s\n", secret);
}
int main(){ decode_and_print(); return 0; }


