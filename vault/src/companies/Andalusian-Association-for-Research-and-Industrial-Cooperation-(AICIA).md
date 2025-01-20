```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Andalusian Association for Research and Industrial Cooperation (AICIA)"
sort location, dt_announce desc
```
