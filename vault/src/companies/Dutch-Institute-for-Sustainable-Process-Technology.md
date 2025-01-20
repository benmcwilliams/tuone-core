```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Dutch Institute for Sustainable Process Technology"
sort location, dt_announce desc
```
