```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "John-Long-Environmental" or company = "John Long Environmental")
sort location, dt_announce desc
```
