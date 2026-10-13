// Statements nested 20 deep (if, while, do, for, switch in turn).
// expect: exit 20
int main(void)
{
    int n;
    n = 0;
    if (1) {
      while (1) {
        do {
          for (;;) {
            switch (1) { case 1:
              if (1) {
                while (1) {
                  do {
                    for (;;) {
                      switch (1) { case 1:
                        if (1) {
                          while (1) {
                            do {
                              for (;;) {
                                switch (1) { case 1:
                                  if (1) {
                                    while (1) {
                                      do {
                                        for (;;) {
                                          switch (1) { case 1:
                                            n = 20;
                                          }
                                        break; }
                                      } while (0);
                                    break; }
                                  }
                                }
                              break; }
                            } while (0);
                          break; }
                        }
                      }
                    break; }
                  } while (0);
                break; }
              }
            }
          break; }
        } while (0);
      break; }
    }
    return n;
}
