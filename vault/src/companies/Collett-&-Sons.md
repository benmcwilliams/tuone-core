```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Collett-&-Sons" or company = "Collett & Sons")
sort location, dt_announce desc
```
