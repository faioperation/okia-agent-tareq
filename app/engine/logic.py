class ScoringEngine:
    @staticmethod
    def evaluate(extracted_json: dict, rules: dict):
        score = 0
        missing = []
        
        # 1. Experience Calculation
        # Extracting years from AI response (converting to float for safety)
        try:
            years = int(extracted_json.get("total_years_exp", 0))
        except:
            years = 0
            
        min_years = int(rules.get("min_years_exp", 0))
        
        if years >= min_years:
            score += 40
        else:
            missing.append(f"Insufficient experience: {years} years found, {min_years} required.")

        # 2. Advanced Skill Matching (Case-insensitive & Partial Match)
        req_skills = [s.lower().strip() for s in rules.get("required_skills", [])]
        
        # Combine all extracted skills into one text for searching
        candidate_skills_list = extracted_json.get("skills", [])
        candidate_skills_text = " ".join([str(s).lower() for s in candidate_skills_list])
        
        match_count = 0
        if req_skills:
            for skill in req_skills:
                # Check if the required skill exists anywhere in the extracted skills text
                if skill in candidate_skills_text:
                    match_count += 1
                else:
                    missing.append(f"Missing skill: {skill}")
            
            # Calculate 60% weight for skills
            skill_score = (match_count / len(req_skills)) * 60
            score += skill_score

        # Construct Final Response Dictionary
        return {
            "result": score >= 60,
            "score": int(score),
            "experience": years,
            "missing_data": missing,
            "analysis_summary": f"Matched {match_count} required skills with {years} years of total experience."
        }