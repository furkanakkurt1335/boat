use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A single word/token line in CoNLL-U format (10 tab-separated fields).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WordLine {
    pub id_f: String,
    pub form: String,
    pub lemma: String,
    pub upos: String,
    pub xpos: String,
    pub feats: String,
    pub head: String,
    pub deprel: String,
    pub deps: String,
    pub misc: String,
}

/// A parsed sentence from a CoNLL-U file.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sentence {
    pub order: usize,
    pub sent_id: String,
    pub text: String,
    pub comments: HashMap<String, String>,
    pub wordlines: Vec<WordLine>,
}

/// Parse CoNLL-U text into a list of sentences.
///
/// Sentences are separated by blank lines. Comment lines start with `#`.
/// Word lines have exactly 10 tab-separated fields.
pub fn parse(content: &str) -> Vec<Sentence> {
    let mut sentences = Vec::new();
    let mut order: usize = 0;

    // Split on one or more blank lines
    for block in content.split("\n\n") {
        let block = block.trim();
        if block.is_empty() {
            continue;
        }

        let mut sent_id = String::new();
        let mut text = String::new();
        let mut comments = HashMap::new();
        let mut wordlines = Vec::new();

        for line in block.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }

            if line.starts_with('#') {
                // Parse comment: # key = value
                if let Some(rest) = line.strip_prefix('#') {
                    if let Some((key, value)) = rest.split_once('=') {
                        let key = key.trim();
                        let value = value.trim();
                        match key {
                            "sent_id" => sent_id = value.to_string(),
                            "text" => text = value.to_string(),
                            _ => {
                                comments.insert(key.to_string(), value.to_string());
                            }
                        }
                    }
                }
            } else {
                // Word line: 10 tab-separated fields
                let cols: Vec<&str> = line.split('\t').collect();
                if cols.len() >= 10 {
                    wordlines.push(WordLine {
                        id_f: cols[0].to_string(),
                        form: cols[1].to_string(),
                        lemma: cols[2].to_string(),
                        upos: cols[3].to_string(),
                        xpos: cols[4].to_string(),
                        feats: cols[5].to_string(),
                        head: cols[6].to_string(),
                        deprel: cols[7].to_string(),
                        deps: cols[8].to_string(),
                        misc: cols[9].to_string(),
                    });
                }
            }
        }

        // Only add if we found word lines (skip empty blocks)
        if !wordlines.is_empty() {
            order += 1;
            sentences.push(Sentence {
                order,
                sent_id,
                text,
                comments,
                wordlines,
            });
        }
    }

    sentences
}

/// Export sentences back to CoNLL-U text.
pub fn export(sentences: &[Sentence]) -> String {
    let mut output = Vec::new();

    for sent in sentences {
        output.push(format!("# sent_id = {}", sent.sent_id));
        output.push(format!("# text = {}", sent.text));
        for (key, value) in &sent.comments {
            output.push(format!("# {} = {}", key, value));
        }

        let sorted = sort_wordlines(&sent.wordlines);
        for wl in &sorted {
            output.push(format!(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
                wl.id_f, wl.form, wl.lemma, wl.upos, wl.xpos, wl.feats, wl.head, wl.deprel,
                wl.deps, wl.misc
            ));
        }
        output.push(String::new()); // blank line between sentences
    }

    let mut result = output.join("\n");
    if !result.is_empty() {
        result.push('\n');
    }
    result
}

/// Sort wordlines by CoNLL-U ID order, placing multiword tokens before their parts.
fn sort_wordlines(wordlines: &[WordLine]) -> Vec<&WordLine> {
    let mut id_map: HashMap<&str, &WordLine> = HashMap::new();
    for wl in wordlines {
        id_map.insert(&wl.id_f, wl);
    }

    let mut result = Vec::new();
    let max_id = wordlines.len() * 5; // generous upper bound

    for i in 1..=max_id {
        // Check for multiword token (e.g., "1-2")
        // We need to check all possible ranges starting at i
        for j in (i + 1)..=(i + 10) {
            let mwt_key = format!("{}-{}", i, j);
            if let Some(wl) = id_map.get(mwt_key.as_str()) {
                result.push(*wl);
            }
        }
        // Check for the single token
        let single_key = i.to_string();
        if let Some(wl) = id_map.get(single_key.as_str()) {
            result.push(*wl);
            // Check for empty nodes (e.g., "1.1")
            for sub in 1..=5 {
                let empty_key = format!("{}.{}", i, sub);
                if let Some(ewl) = id_map.get(empty_key.as_str()) {
                    result.push(*ewl);
                }
            }
        } else if result.len() >= wordlines.len() {
            break;
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_basic() {
        let input = "\
# sent_id = test_1
# text = Hello world.
1\tHello\thello\tINTJ\t_\t_\t0\troot\t_\t_
2\tworld\tworld\tNOUN\t_\tNumber=Sing\t1\tvocative\t_\tSpaceAfter=No
3\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\tSpacesAfter=\\n
";
        let sents = parse(input);
        assert_eq!(sents.len(), 1);
        assert_eq!(sents[0].sent_id, "test_1");
        assert_eq!(sents[0].text, "Hello world.");
        assert_eq!(sents[0].wordlines.len(), 3);
        assert_eq!(sents[0].order, 1);
    }

    #[test]
    fn test_parse_multiword() {
        let input = "\
# sent_id = mwt_1
# text = Test.
1-2\tAB\t_\t_\t_\t_\t_\t_\t_\t_
1\tA\ta\tNOUN\t_\t_\t0\troot\t_\t_
2\tB\tb\tAUX\t_\t_\t1\tcop\t_\t_
";
        let sents = parse(input);
        assert_eq!(sents[0].wordlines.len(), 3);
        assert_eq!(sents[0].wordlines[0].id_f, "1-2");
    }

    #[test]
    fn test_roundtrip() {
        let input = "\
# sent_id = rt_1
# text = Test.
1\tTest\ttest\tNOUN\t_\t_\t0\troot\t_\tSpaceAfter=No
2\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\tSpacesAfter=\\n

# sent_id = rt_2
# text = Hello.
1\tHello\thello\tINTJ\t_\t_\t0\troot\t_\tSpaceAfter=No
2\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\tSpacesAfter=\\n
";
        let sents = parse(input);
        assert_eq!(sents.len(), 2);
        let exported = export(&sents);
        let reparsed = parse(&exported);
        assert_eq!(reparsed.len(), 2);
        assert_eq!(reparsed[0].sent_id, "rt_1");
        assert_eq!(reparsed[1].sent_id, "rt_2");
    }
}
