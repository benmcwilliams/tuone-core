```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "University-College-London" or company = "University College London")
sort location, dt_announce desc
```
