import pandas as pd 
from Bio import SeqIO
import subprocess
from io import StringIO
import pdb 

class Matcher:
    """
    A BLAST-based sequence matcher for identifying exact or high-probability matches 
    to a reference database using nucleotide identity and alignment length criteria.
    """
    
    def __init__(self, ref_db, exact_match_threshold=99.9, match_len_threshold=0.9, high_prob_threshold=94):
        """
        Initialize the Matcher with configurable thresholds and a reference BLAST database.

        Args:
            exact_match_threshold (float): Minimum % identity for an exact match.
            match_len_threshold (float): Minimum fraction of query length that must align.
            high_prob_threshold (float): Threshold for high-probability matches (avg identity).
            ref_db (str): Path to the reference BLAST database.
        """
        self.ref_db = ref_db  
        self.exact_match_threshold = exact_match_threshold
        self.match_len_threshold = match_len_threshold
        self.high_prob_threshold = high_prob_threshold 

    @staticmethod
    def get_longest_hits(blast_df):
        """
        Get the longest alignment per subject from the BLAST results.

        Args:
            blast_df (pd.DataFrame): BLAST output dataframe.

        Returns:
            pd.DataFrame: Subset of entries with max alignment length per subject.
        """
        idx = blast_df.groupby('subject_id')['alignment_len'].idxmax()
        return blast_df.loc[idx].reset_index(drop=True).sort_values('%_identity', ascending=False)
    
    @staticmethod
    def get_sequence_len(seq_file):
        """
        Extract sequence length from a FASTA file.

        Args:
            seq_file (str): Path to the query FASTA file.

        Returns:
            int: Length of the sequence.
        """
        return len(next(SeqIO.parse(seq_file, "fasta")).seq)
    
    @staticmethod
    def aggregate_identities(blast_df):
        """
        Compute average identity per subject, weighted by alignment length.

        Args:
            blast_df (pd.DataFrame): BLAST output dataframe.

        Returns:
            pd.DataFrame: Aggregated identity values per subject.
        """
        aggregated_identity = (
            blast_df
            .assign(weighted_identity=blast_df["%_identity"] * blast_df["alignment_len"])
            .groupby(["query_id", "subject_id"], as_index=False)
            .agg({
                "weighted_identity": "sum",
                "alignment_len": "sum"
            })
            .assign(avg_identity=lambda df: df["weighted_identity"] / df["alignment_len"])
            .drop(columns=["weighted_identity", "alignment_len"])
            .sort_values("avg_identity", ascending=False)
        )

        return aggregated_identity
    
    def blast(self, query_file):
        """
        Run BLASTN for the given query file against the reference database.

        Args:
            query_file (str): Path to the query FASTA file.

        Returns:
            pd.DataFrame: Parsed BLAST tabular output.
        """
        blast_command = [
            "blastn",
            "-query", query_file,
            "-db", self.ref_db,
            "-outfmt", "6"
        ]
        result = subprocess.run(blast_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        blast_output = StringIO(result.stdout)
        blast_df = pd.read_csv(blast_output, header=None, names=[
            'query_id', 'subject_id', '%_identity', 'alignment_len', 'mismatches', 'gap_opens', 
            'query_start', 'query_end', 'subject_start', 'subject_end', 'e_value', 'bit_score'
        ], sep='\t')
        return blast_df
    
    def has_exact_match(self, blast_df, seq_len):
        """
        Determine whether an exact match exists in the BLAST results.

        Args:
            blast_df (pd.DataFrame): BLAST results.
            seq_len (int): Length of the query sequence.

        Returns:
            bool: True if exact match is found, else False.
        """
        exact_match = blast_df[
            (blast_df['%_identity'] >= self.exact_match_threshold) &
            (blast_df['alignment_len'] >= seq_len * self.match_len_threshold)
        ]
        return len(exact_match) > 0

    def get_exact_matches(self, blast_df, seq_len):
        """
        Return all exact matches from the BLAST results.

        Args:
            blast_df (pd.DataFrame): BLAST results.
            seq_len (int): Length of the query sequence.

        Returns:
            pd.DataFrame: Filtered DataFrame of exact matches.
        """
        return blast_df[
            (blast_df['%_identity'] >= self.exact_match_threshold) &
            (blast_df['alignment_len'] >= seq_len * self.match_len_threshold)
        ]

    def filter_high_prob_hits(self, blast_df):
        """
        Filter hits with average identity above the high probability threshold.

        Args:
            blast_df (pd.DataFrame): Aggregated identity DataFrame.

        Returns:
            pd.DataFrame: High-confidence hits.
        """
        return blast_df[blast_df["avg_identity"] >= self.high_prob_threshold]
    
    def match(self, query_file):
        """
        Perform the full matching pipeline:
        - Run BLAST
        - Check for exact matches
        - If none, compute and return high-confidence matches

        Args:
            query_file (str): Path to query FASTA file.

        Returns:
            tuple:
                - bool: True if exact match found, else False
                - list of tuples: [(subject_id, identity), ...]
        """
        blast_df = self.blast(query_file)
        seq_len = self.get_sequence_len(query_file)
        if self.has_exact_match(blast_df, seq_len):
            matches = self.get_exact_matches(blast_df, seq_len)
            match_ids = matches['subject_id'].values
            match_probs = matches['%_identity'].values
            return True, list(zip(match_ids, match_probs))
        else:
            agg_identities = self.aggregate_identities(blast_df)
            high_probs = self.filter_high_prob_hits(agg_identities)
            match_ids = high_probs['subject_id'].values
            match_probs = high_probs['avg_identity'].values
            return False, list(zip(match_ids, match_probs))
    

if __name__ == "__main__":
    matcher = Matcher()
    exact, matches = matcher.match("test_sequence_high_prob.fasta")
    print(exact, matches)


