import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importTickets } from '../api/client';

export function useImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      autoClassify,
    }: {
      file: File;
      autoClassify?: boolean;
    }) => importTickets(file, autoClassify),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tickets'] }),
  });
}
