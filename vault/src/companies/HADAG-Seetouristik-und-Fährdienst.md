```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "HADAG-Seetouristik-und-Fährdienst" or company = "HADAG Seetouristik und Fährdienst")
sort location, dt_announce desc
```
