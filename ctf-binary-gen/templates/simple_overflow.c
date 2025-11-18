#include <stdio.h>
#include <string.h>
int vuln() {
    char small[16];
    gets(small); // intentionally unsafe for RE exercise
    return 0;
}
int main(){
    puts("Send input:");
    vuln();
    puts("done");
    return 0;
}


