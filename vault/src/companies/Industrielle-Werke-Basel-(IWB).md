```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Industrielle Werke Basel (IWB)"
sort location, dt_announce desc
```
