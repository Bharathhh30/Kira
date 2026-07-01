from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None


class ResumeLinks(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    leetcode: str | None = None
    codeforces: str | None = None
    other: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str
    title: str | None = None
    start_date: str | None = None  # YYYY-MM format
    end_date: str | None = None  # YYYY-MM or "current"
    location: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    github_url: str | None = None


class EducationEntry(BaseModel):
    institution: str
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: float | None = None
    honors: list[str] = Field(default_factory=list)


class SkillSet(BaseModel):
    technical: list[str] = Field(default_factory=list)
    languages_spoken: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    github_url: str | None = None
    live_url: str | None = None
    dates: str | None = None


class CertificationEntry(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None
    url: str | None = None


class CodingProfiles(BaseModel):
    leetcode_rating: str | None = None
    codechef_rating: str | None = None
    codeforces_rating: str | None = None


class ResumeOutput(BaseModel):
    personal: PersonalInfo | None = None
    links: ResumeLinks | None = None
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: SkillSet | None = None
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    coding_profiles: CodingProfiles | None = None

    model_config = {"populate_by_name": True, "str_strip_whitespace": True}
