```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ikigai-Capital" or company = "Ikigai Capital")
sort location, dt_announce desc
```
