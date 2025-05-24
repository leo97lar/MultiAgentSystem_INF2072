import re
from typing import List, Pattern

PHRASES = [
    r"i have",
    r"i've",
    r"ive",
    r"i'm",
    r"suffering from",
    r"suffer from",
    r"being",
    r"diagnosis of",
    r"diagnosed with",
    r"diagnosed me with",
    r"diagnostic of",
    r"diagnosis is"
    r"diagnosed",
    r"hospitalized with",
    r"hospital with",
    r"my",
    r"live with",
    r"living with",
    r"as a",
    r"as"
]

# Intellectual Developmental Disorder (Intellectual Disability)
DISORDERS_INTELLECTUAL = [
    'intellectual disability', 'intellectual developmental', 'idd', 'mental retardation',
    'developmental delay', 'developmental disabilit', 'hypertelorism', 'facies',
    'snijders', 'child development deviation', 'development deviation', 'mental deficiency'
]

# Language Disorder
DISORDERS_LANGUAGE = [
    'language disorder', 'language', 'speech delay', 'expressive language', 'receptive language', 'aphasia',
    'acquired language disorder', 'language impairment', 'speech disorder',
    'specific language disorder', 'sld', 'developmental disorder', 'language delay',
    'semantic-pragmatic', 'semantic pragmatic', 'central auditory', 'auditory central',
    'speech or language developmental'
]

# Speech Sound Disorder
DISORDERS_SPEECH_SOUND = [
    'speech sound disorder', 'speech sound', 'articulation', 'phonological', 'apraxia', 'dysarthria'
]

# Social (Pragmatic) Communication Disorder
DISORDERS_PRAGMATIC = [
    'social communication disorder', 'social communication', 'pragmatic', 'social language'
]

# Unspecified Communication Disorder
DISORDERS_COMMUNICATION = [
    'communication disorder', 'communication', 'unspecified communication', 'speech and language',
    'childhood communication', 'acquired communication', 'communicative',
    'developmental communication', 'neurogenic', 'hearing disorder'
]

# Autism Spectrum Disorder
DISORDERS_AUTISM = [
    'autism', 'asd', 'asperger', 'high-functioning autism', 'pervasive developmental disorder',
    'autie', 'autistic', 'kenner', 'cerebroatrophic hyperammonemia', 'rett', 'akinetic'
]

# Bipolar I Disorder
DISORDERS_BIPOLAR_I = [
    'bipolar disorder', 'bipolar', 'manic', 'mania'
]

# Bipolar II Disorder
DISORDERS_BIPOLAR_II = [
    'hypomania'
]

# Cyclothymia
DISORDERS_CYCLOTHYMIA = [
    'cyclothymi'
]

# Factitious Disorder
DISORDERS_FACTITIOUS = [
    'factitious disorder', 'factitious', 'genser syndrome', 'pseudodementia', 'pseudopsychosis'
]

# Alzheimer’s / Dementia
DISORDERS_DEMENTIA = [
    'alzheimer', 'dementia', 'cognitive decline', 'amentia', 'senile paranoid dementia',
    'familial dementia', 'early-onset dementia', 'acute confuse senile', 'early onset alzheimer',
    'familiar alzheimer disease', 'focal onset alzheimer', 'late onset alzheimer',
    'presenile alzheimer', 'primary senile degenerative dementia', 'senile dementia'
]

# Brain Injury
DISORDERS_BRAIN_INJURY = [
    'brain injury', 'traumatic brain injury', 'tbi', 'concussion', 'head injury',
    'focal brain inj', 'acute brain inj', 'brain laceration', 'chronic brain inj'
]

# Lewy Body Disease
DISORDERS_LEWY_BODY = [
    'lewy body disease', 'lewy body dementia', 'lbd', 'cortical lewy body disease',
    'diffuse lewy body', 'lewy bod'
]

# Frontotemporal Lobar Degeneration
DISORDERS_FTLD = [
    'frontotemporal lobar degeneration', 'ftld', 'frontotemporal dementia', "pick's disease",
    'ddpac', "familial pick's disease", 'hddd', 'semantic dementia', 'wilhelmsen-lynch disease',
    'hereditary dysphasic disinhibition dementia', 'multiple system tauopathy with presenile dementia'
]

# Parkinson’s Disease
DISORDERS_PARKINSON = [
    "parkinson's disease", 'parkinson', 'parkinsonism', 'parkinsonian syndrome', 'idiopathic parkinson',
    'paralysis agitans', 'primary parkinsonism'
]

# Huntington’s Disease
DISORDERS_HUNTINGTON = [
    "huntington's disease", 'huntington', 'akinetic-rigid variant of huntington', 'chorea',
    'chronic progressive hereditary chorea', 'juvenile huntington', 'juvenile-onset huntington',
    'late-onset huntington disease', 'late onset huntington disease', 'juvenile onset huntington',
    'progressive chorea'
]

# Specific Learning Disorder
DISORDERS_LEARNING = [
    'learning disorder', 'specific learning', 'learning', 'dyslexia', 'dysgraphia', 'dyscalculia', 'sld'
]

# Borderline Personality Disorder
DISORDERS_BPD = [
    'borderline personality disorder', 'borderline', 'bpd', 'bp-d'
]

DISORDERS_SZ = [
    'schizophrenia', 'schizophren', 'schizoaffective', 'schizotypal', 'delusional disorder',
    'paranoia', 'psychosis', 'psychotic', 'hallucinat', 'delusion',
    'catatonia', 'paranoid schizophrenia', 'disorganized schizophrenia',
    'schizophreniform'
]

def build_declaration_patterns(disorder_terms: List[str], phrases: List[str]) -> List[str]:
    """
    Combines phrases with disorder-related terms to create regex patterns.
    """
    patterns = [fr"{phrase}\s*({disorder})" for phrase in phrases for disorder in disorder_terms]
    combined_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    return combined_patterns

def find_declaration_patterns(pattern_type: str = 'sz') -> List[Pattern]:
    """
    Returns compiled regex patterns for the given mental health declaration type.
    Available types: 'sz' for schizophrenia, 'bp' for bipolar disorder and many others.
    """
    pattern_type = pattern_type.lower()

    if pattern_type == 'sz':
        disorder_terms = DISORDERS_SZ
    elif pattern_type == 'bp':
        disorder_terms = DISORDERS_BIPOLAR_I + DISORDERS_BIPOLAR_II + DISORDERS_CYCLOTHYMIA
    else:
        raise ValueError(f"Unsupported pattern_type: {pattern_type}")

    return build_declaration_patterns(disorder_terms, PHRASES)

def find_all_but_one_patterns(excluded_type: str) -> List[Pattern]:
    """
    Returns compiled regex patterns for all mental health declaration types
    except the one specified by `excluded_type`.

    Parameters:
        excluded_type (str): The key of the disorder to exclude (e.g., 'sz', 'bp').

    Returns:
        List[Pattern]: Compiled regex patterns.
    """
    disorder_map = {
        'sz': DISORDERS_SZ,
        'bp': DISORDERS_BIPOLAR_I + DISORDERS_BIPOLAR_II + DISORDERS_CYCLOTHYMIA,
        'intellectual': DISORDERS_INTELLECTUAL,
        'language': DISORDERS_LANGUAGE,
        'speech_sound': DISORDERS_SPEECH_SOUND,
        'pragmatic': DISORDERS_PRAGMATIC,
        'communication': DISORDERS_COMMUNICATION,
        'autism': DISORDERS_AUTISM,
        'factitious': DISORDERS_FACTITIOUS,
        'dementia': DISORDERS_DEMENTIA,
        'brain_injury': DISORDERS_BRAIN_INJURY,
        'lewy_body': DISORDERS_LEWY_BODY,
        'ftld': DISORDERS_FTLD,
        'parkinson': DISORDERS_PARKINSON,
        'huntington': DISORDERS_HUNTINGTON,
        'learning': DISORDERS_LEARNING,
        'bpd': DISORDERS_BPD,
    }

    excluded_type = excluded_type.lower()
    if excluded_type not in disorder_map:
        raise ValueError(f"Unsupported excluded_type: {excluded_type}")

    # Combine all disorders except the excluded one
    combined_disorders = []
    for key, disorder_list in disorder_map.items():
        if key != excluded_type:
            combined_disorders.extend(disorder_list)

    return build_declaration_patterns(combined_disorders, PHRASES)


def get_flair_pattern_for_disorder(disorder_type: str) -> Pattern:
    """
    Returns a compiled regex pattern matching any flair term for the given disorder type.

    Parameters:
        disorder_type (str): Key of the disorder (e.g., 'sz', 'bp', etc.).

    Returns:
        Pattern: A compiled regex pattern matching any term in the disorder.
                 Returns a regex that matches nothing if disorder_type not found.
    """
    disorder_map = {
        'sz': DISORDERS_SZ,
        'bp': DISORDERS_BIPOLAR_I + DISORDERS_BIPOLAR_II + DISORDERS_CYCLOTHYMIA,
        'intellectual': DISORDERS_INTELLECTUAL,
        'language': DISORDERS_LANGUAGE,
        'speech_sound': DISORDERS_SPEECH_SOUND,
        'pragmatic': DISORDERS_PRAGMATIC,
        'communication': DISORDERS_COMMUNICATION,
        'autism': DISORDERS_AUTISM,
        'factitious': DISORDERS_FACTITIOUS,
        'dementia': DISORDERS_DEMENTIA,
        'brain_injury': DISORDERS_BRAIN_INJURY,
        'lewy_body': DISORDERS_LEWY_BODY,
        'ftld': DISORDERS_FTLD,
        'parkinson': DISORDERS_PARKINSON,
        'huntington': DISORDERS_HUNTINGTON,
        'learning': DISORDERS_LEARNING,
        'bpd': DISORDERS_BPD,
    }

    keywords = disorder_map.get(disorder_type.lower(), [])
    if not keywords:
        # If no keywords found, return a pattern that matches nothing
        return re.compile(r'a^')  # matches nothing

    # Join all keywords into one regex pattern separated by '|'
    # Escape keywords in case they contain special regex chars
    escaped_keywords = [re.escape(k) for k in keywords]
    combined_pattern = r'(' + '|'.join(escaped_keywords) + r')'

    # Compile with ignore case flag
    return re.compile(combined_pattern, flags=re.IGNORECASE)


def get_term_for_disorder(disorder_type: str):
    """
    Returns the first term for the given disorder type from the disorder map.

    Parameters:
        disorder_type (str): Key of the disorder (e.g., 'sz', 'bp', etc.).

    Returns:
        str or None: The first term in the list of terms for the disorder,
                     or None if disorder not found or list empty.
    """
    disorder_map = {
        'sz': DISORDERS_SZ,
        'bp': DISORDERS_BIPOLAR_I + DISORDERS_BIPOLAR_II + DISORDERS_CYCLOTHYMIA,
        'intellectual': DISORDERS_INTELLECTUAL,
        'language': DISORDERS_LANGUAGE,
        'speech_sound': DISORDERS_SPEECH_SOUND,
        'pragmatic': DISORDERS_PRAGMATIC,
        'communication': DISORDERS_COMMUNICATION,
        'autism': DISORDERS_AUTISM,
        'factitious': DISORDERS_FACTITIOUS,
        'dementia': DISORDERS_DEMENTIA,
        'brain_injury': DISORDERS_BRAIN_INJURY,
        'lewy_body': DISORDERS_LEWY_BODY,
        'ftld': DISORDERS_FTLD,
        'parkinson': DISORDERS_PARKINSON,
        'huntington': DISORDERS_HUNTINGTON,
        'learning': DISORDERS_LEARNING,
        'bpd': DISORDERS_BPD,
    }

    terms = disorder_map.get(disorder_type)
    if terms and len(terms) > 0:
        return terms[0]
    else:
        return None


def get_disorder_for_term(term: str):# -> str | None:
    """
    Given a term, return the disorder key whose list contains that term.

    Parameters:
        term (str): The term to search for.

    Returns:
        str or None: The key of the disorder list containing the term,
                     or None if the term is not found in any list.
    """
    disorder_map = {
        'sz': DISORDERS_SZ,
        'bp': DISORDERS_BIPOLAR_I + DISORDERS_BIPOLAR_II + DISORDERS_CYCLOTHYMIA,
        'intellectual': DISORDERS_INTELLECTUAL,
        'language': DISORDERS_LANGUAGE,
        'speech_sound': DISORDERS_SPEECH_SOUND,
        'pragmatic': DISORDERS_PRAGMATIC,
        'communication': DISORDERS_COMMUNICATION,
        'autism': DISORDERS_AUTISM,
        'factitious': DISORDERS_FACTITIOUS,
        'dementia': DISORDERS_DEMENTIA,
        'brain_injury': DISORDERS_BRAIN_INJURY,
        'lewy_body': DISORDERS_LEWY_BODY,
        'ftld': DISORDERS_FTLD,
        'parkinson': DISORDERS_PARKINSON,
        'huntington': DISORDERS_HUNTINGTON,
        'learning': DISORDERS_LEARNING,
        'bpd': DISORDERS_BPD,
    }

    for disorder_key, terms_list in disorder_map.items():
        if term in terms_list:
            return disorder_key
    return None