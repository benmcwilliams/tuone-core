```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Fern-Communications" or company = "Fern Communications")
sort location, dt_announce desc
```
