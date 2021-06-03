#include "two-matrix-ifc.h"

void outsource(struct Input *input, struct Output *output)
{
	int i, j, k;
	int t;
	int kk;
	for (i=0; i<SIZE; i+=1)
	{
		for (j=0; j<SIZE; j+=1)
		{
			t = 0;
			for (k=0; k<SIZE; k+=1)
			{
				kk = MAT(input->a, i, k) * MAT(input->b, k, j);
				kk = kk / 10000000;
				t = t + kk;
			}
			MAT(output->r, i, j) = t;
		}
	}
}
