```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Oil'Ive-Green" or company = "Oil'Ive Green")
sort location, dt_announce desc
```
