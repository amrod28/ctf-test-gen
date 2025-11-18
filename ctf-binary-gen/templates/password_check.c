#include <stdio.h>
#include <string.h>
int check(const char *p) {
    return strcmp(p, "{FLAG}") == 0;
}
int main(){
    char buf[128];
    printf("Enter password: ");
    if(!fgets(buf, sizeof(buf), stdin)) return 1;
    buf[strcspn(buf, "\n")] = 0;
    if(check(buf)) printf("OK\\n"); else printf("NO\\n");
    return 0;
}


