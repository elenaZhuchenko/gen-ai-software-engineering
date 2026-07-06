import { useMutation, useQueryClient } from '@tanstack/react-query';
import { autoClassify } from '../api/client';

export function useAutoClassify() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, override }: { id: string; override?: boolean }) =>
      autoClassify(id, override),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tickets'] }),
  });
}
