import os
import jiwer
import pandas as pd
import tempfile
import zipfile

PUNCTUATION = ",.!?，。！？"
WINDOW = 5

def remove_punct(s):
    for punct in PUNCTUATION:
        s = s.replace(punct, "")
    return s

def split_transcript_by_prefix(transcript):
    transcripts = {'L': [], 'R': [], 'B': []}
    lines = transcript.strip().split('\n')
    for line in lines:
        tokens = line.strip().split()
        if not tokens:
            continue
        if tokens[0] in {'L', 'R', 'B'}:
            prefix = tokens[0]
            content = ' '.join(tokens[1:])
        else:
            prefix = 'B'
            content = ' '.join(tokens)

        content = remove_punct(content.lower())
        content = ' '.join(content.split()[2:])
        transcripts[prefix].append(content)
    for key in transcripts:
        transcripts[key] = ' '.join(transcripts[key])
    return transcripts

def get_dtl(alignments, ref, hyp, correct, substitutions, deletions, insertions):
    for chunk in alignments:
        if chunk.type == "equal":
            for i in range(chunk.ref_start_idx, chunk.ref_end_idx):
                word = ref[i]
                correct[word] = correct.get(word, 0) + 1
        elif chunk.type == "substitute":
            for i, j in zip(range(chunk.ref_start_idx, chunk.ref_end_idx),
                            range(chunk.hyp_start_idx, chunk.hyp_end_idx)):
                src = ref[i]
                dst = hyp[j]
                substitutions[(src, dst)] = substitutions.get((src, dst), 0) + 1
        elif chunk.type == "delete":
            for i in range(chunk.ref_start_idx, chunk.ref_end_idx):
                src = ref[i]
                deletions[src] = deletions.get(src, 0) + 1
        elif chunk.type == "insert":
            for j in range(chunk.hyp_start_idx, chunk.hyp_end_idx):
                dst = hyp[j]
                insertions[dst] = insertions.get(dst, 0) + 1

def get_alignments(wer_output, filename, prefix):
    ref_words = []
    hyp_words = []
    error_types = []

    for chunk in wer_output.alignments[0]:
        if chunk.type == "delete":
            for i in range(chunk.ref_start_idx, chunk.ref_end_idx):
                src = wer_output.references[0][i]
                ref_words.append(src)
                hyp_words.append("*" * len(src))
                error_types.append(chunk.type)
        elif chunk.type == "insert":
            for i in range(chunk.hyp_start_idx, chunk.hyp_end_idx):
                dst = wer_output.hypotheses[0][i]
                ref_words.append("*" * len(dst))
                hyp_words.append(dst)
                error_types.append(chunk.type)
        else:
            for i, j in zip(range(chunk.ref_start_idx, chunk.ref_end_idx),
                            range(chunk.hyp_start_idx, chunk.hyp_end_idx)):
                src = wer_output.references[0][i]
                dst = wer_output.hypotheses[0][j]
                max_len = max(len(src), len(dst))
                ref_words.append(src.rjust(max_len))
                hyp_words.append(dst.rjust(max_len))
                error_types.append(chunk.type)

    errors = []

    for i, (src, dst, err) in enumerate(zip(ref_words, hyp_words, error_types)):
        if err == "equal":
            continue
        min_i = max(0, i - WINDOW)
        max_i = min(len(ref_words), i + WINDOW + 1)
        errors.append((
            filename,
            prefix,
            " ".join(ref_words[min_i:i]),
            ref_words[i],
            " ".join(ref_words[i+1:max_i]),
            " ".join(hyp_words[min_i:i]),
            hyp_words[i],
            " ".join(hyp_words[i+1:max_i]),
            err
        ))

    return errors

def process_pair(ref_transcript, hyp_transcript, filename):
    if not ref_transcript.strip() or not hyp_transcript.strip():
        return None

    ref_segments = split_transcript_by_prefix(ref_transcript)
    hyp_segments = split_transcript_by_prefix(hyp_transcript)

    combined_results = {
        'filename': filename,
        'alignments': [],
        'stats': [],
        'errors': [],
        'correct': {},
        'substitutions': {},
        'deletions': {},
        'insertions': {}
    }

    prefixes = ['L', 'R', 'B']

    for prefix in prefixes:
        ref = ref_segments.get(prefix, '')
        hyp = hyp_segments.get(prefix, '')

        if not ref.strip() or not hyp.strip():
            continue

        wer_output = jiwer.process_words(ref, hyp)

        correct = {}
        substitutions = {}
        deletions = {}
        insertions = {}

        get_dtl(
            wer_output.alignments[0],
            wer_output.references[0],
            wer_output.hypotheses[0],
            correct,
            substitutions,
            deletions,
            insertions
        )

        errors = get_alignments(wer_output, filename, prefix)

        alignment = jiwer.visualize_alignment(wer_output)
        wer = wer_output.wer
        cor = wer_output.hits
        sub = wer_output.substitutions
        ins = wer_output.insertions
        dele = wer_output.deletions

        stats = {
            "id": filename,
            "prefix": prefix,
            "wer": wer,
            "correct": cor,
            "substitutions": sub,
            "insertions": ins,
            "deletions": dele
        }

        combined_results['alignments'].append((filename, prefix, alignment))
        combined_results['stats'].append(stats)
        combined_results['errors'].extend(errors)

        for word, count in correct.items():
            combined_results['correct'][word] = combined_results['correct'].get(word, 0) + count
        for pair, count in substitutions.items():
            combined_results['substitutions'][pair] = combined_results['substitutions'].get(pair, 0) + count
        for word, count in deletions.items():
            combined_results['deletions'][word] = combined_results['deletions'].get(word, 0) + count
        for word, count in insertions.items():
            combined_results['insertions'][word] = combined_results['insertions'].get(word, 0) + count

    return combined_results

def generate_summary_and_zip(results):
    output_dir = tempfile.mkdtemp()
    output_files = []
    stats_list = []
    alignment_list = []
    errors = []
    correct = {}
    substitutions = {}
    deletions = {}
    insertions = {}

    for res in results:
        filename = res['filename']
        stats = res['stats']
        alignments = res['alignments']
        errors.extend(res['errors'])

        for word, count in res['correct'].items():
            correct[word] = correct.get(word, 0) + count
        for pair, count in res['substitutions'].items():
            substitutions[pair] = substitutions.get(pair, 0) + count
        for word, count in res['deletions'].items():
            deletions[word] = deletions.get(word, 0) + count
        for word, count in res['insertions'].items():
            insertions[word] = insertions.get(word, 0) + count

        for stat in stats:
            stats_list.append((
                stat['id'],
                stat['prefix'],
                stat['wer'],
                stat['correct'],
                stat['substitutions'],
                stat['insertions'],
                stat['deletions']
            ))

        for alignment in alignments:
            alignment_list.append(alignment)

    df_stats = pd.DataFrame(
        stats_list,
        columns=["id", "prefix", "wer", "correct", "substitutions", "insertions", "deletions"]
    )
    stats_csv_path = os.path.join(output_dir, "wer_stats.csv")
    df_stats.to_csv(stats_csv_path, index=False)

    wer_results_txt_path = os.path.join(output_dir, "wer_results.txt")
    with open(wer_results_txt_path, "w", encoding='utf-8') as f:
        for filename, prefix, alignment in alignment_list:
            f.write(f"{filename} - Prefix: {prefix}\n{alignment}\n")

    errors_df = pd.DataFrame(
        errors,
        columns=["filename", "prefix", "ref_prev", "ref", "ref_post", "hyp_prev", "hyp", "hyp_post", "type"]
    )
    errors_csv_path = os.path.join(output_dir, "errors_context.csv")
    errors_df.to_csv(errors_csv_path, index=False)
    output_files.append(errors_csv_path)

    conf_data = []
    for corr, count in correct.items():
        conf_data.append((corr, corr, count, "Correct"))
    for src, count in deletions.items():
        conf_data.append((src, 'NIL', count, "Deletions"))
    for (src, dst), count in substitutions.items():
        conf_data.append((src, dst, count, "Substitutions"))
    for dst, count in insertions.items():
        conf_data.append(('NIL', dst, count, "Insertions"))
    dtl = pd.DataFrame(
        conf_data,
        columns=["Source", "Destination", "Count", "Category"]
    )
    dtl = dtl.sort_values(["Source", "Destination"])
    word_errors_csv_path = os.path.join(output_dir, "word_errors.csv")
    dtl.to_csv(word_errors_csv_path, index=False)
    output_files.append(word_errors_csv_path)

    zip_file_path = os.path.join(output_dir, "output.zip")
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file_path in output_files:
            zipf.write(file_path, arcname=os.path.basename(file_path))

    return output_files, zip_file_path
