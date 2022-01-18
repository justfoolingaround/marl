def linguistic_expansion(*content, separator=', ', use_before_last=False, final='and'):
    """
    `a, b, c` -> `a, b and c.`
    """
    *remains, last_value = content
    
    if not remains:
        return last_value

    joined = separator.join(remains)
    
    if use_before_last:
        joined += separator.strip()
        
    return joined + " {} {}".format(final, last_value)
