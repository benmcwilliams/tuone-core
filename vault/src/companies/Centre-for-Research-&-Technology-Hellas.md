```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Centre-for-Research-&-Technology-Hellas" or company = "Centre for Research & Technology Hellas")
sort location, dt_announce desc
```
