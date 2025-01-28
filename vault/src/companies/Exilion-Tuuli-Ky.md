```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Exilion-Tuuli-Ky" or company = "Exilion Tuuli Ky")
sort location, dt_announce desc
```
