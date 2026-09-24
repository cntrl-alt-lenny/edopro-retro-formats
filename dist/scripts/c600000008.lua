--Malefic Blue-Eyes White Dragon (historical implementation, Retro Formats)
--Original script for edopro-retro-formats (MIT). Written from the period card text
--and the engine's Lua API; it is not a copy or an adaptation of any Project Ignis
--CardScripts file, whose licence (AGPL-3.0-or-later) this repository does not carry.
--
--Period text: "This card cannot be Normal Summoned or Set. This card can only be Special
--Summoned by removing from play 1 "Blue-Eyes White Dragon" from your Deck. There can
--only be 1 face-up "Malefic" monster on the field. Other monsters you control cannot
--declare an attack. If there is no face-up Field Spell Card on the field, destroy this
--card."
--
--Implemented: it can never be Normal Summoned or Set, and can be Special Summoned only
--by the procedure below, from the hand, banishing a "Blue-Eyes White Dragon" from the
--Deck. Unlike the modern card, nothing else can ever Special Summon it, so it cannot
--be revived from the Graveyard or the banished zone. Only face-up "Malefic" monsters
--count towards the limit of one.
--See data/custom-cards/c600000008.json for what this script does not reproduce.
local s,id=GetID()
local CARD_BLUE_EYES=89631139
local SET_MALEFIC=0x23
function s.initial_effect(c)
	c:SetUniqueOnField(1,1,s.uqfilter,LOCATION_MZONE)
	--cannot be Normal Summoned or Set
	local e0=Effect.CreateEffect(c)
	e0:SetType(EFFECT_TYPE_SINGLE)
	e0:SetProperty(EFFECT_FLAG_CANNOT_DISABLE+EFFECT_FLAG_UNCOPYABLE)
	e0:SetCode(EFFECT_CANNOT_SUMMON)
	c:RegisterEffect(e0)
	local e1=e0:Clone()
	e1:SetCode(EFFECT_CANNOT_MSET)
	c:RegisterEffect(e1)
	--can only be Special Summoned by its own procedure
	local e2=Effect.CreateEffect(c)
	c:EnableReviveLimit()
	--Special Summon from the hand by banishing "Blue-Eyes White Dragon" from the Deck
	local e3=Effect.CreateEffect(c)
	e3:SetType(EFFECT_TYPE_FIELD)
	e3:SetProperty(EFFECT_FLAG_UNCOPYABLE)
	e3:SetCode(EFFECT_SPSUMMON_PROC)
	e3:SetRange(LOCATION_HAND)
	e3:SetCondition(s.spcon)
	e3:SetOperation(s.spop)
	c:RegisterEffect(e3)
	--other monsters you control cannot declare an attack
	local e4=Effect.CreateEffect(c)
	e4:SetType(EFFECT_TYPE_FIELD)
	e4:SetCode(EFFECT_CANNOT_ATTACK_ANNOUNCE)
	e4:SetRange(LOCATION_MZONE)
	e4:SetTargetRange(LOCATION_MZONE,0)
	e4:SetTarget(s.atktg)
	c:RegisterEffect(e4)
	--destroy this card if there is no face-up Field Spell Card on the field
	local e5=Effect.CreateEffect(c)
	e5:SetType(EFFECT_TYPE_SINGLE)
	e5:SetProperty(EFFECT_FLAG_CANNOT_DISABLE)
	e5:SetCode(EFFECT_SELF_DESTROY)
	e5:SetRange(LOCATION_MZONE)
	e5:SetCondition(s.sdcon)
	c:RegisterEffect(e5)
end
function s.uqfilter(c)
	return c:IsSetCard(SET_MALEFIC)
end
function s.rmfilter(c)
	return c:IsCode(CARD_BLUE_EYES) and c:IsAbleToRemoveAsCost()
end
function s.spcon(e,c)
	if c==nil then return true end
	local tp=c:GetControler()
	return Duel.GetLocationCount(tp,LOCATION_MZONE)>0
		and Duel.IsExistingMatchingCard(s.rmfilter,tp,LOCATION_DECK,0,1,nil)
end
function s.spop(e,tp,eg,ep,ev,re,r,rp,c)
	Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_REMOVE)
	local g=Duel.SelectMatchingCard(tp,s.rmfilter,tp,LOCATION_DECK,0,1,1,nil)
	Duel.Remove(g,POS_FACEUP,REASON_COST)
end
function s.atktg(e,c)
	return c~=e:GetHandler()
end
function s.fieldfilter(c)
	return c:IsFaceup() and c:IsType(TYPE_FIELD)
end
function s.sdcon(e)
	return not Duel.IsExistingMatchingCard(s.fieldfilter,0,LOCATION_FZONE,LOCATION_FZONE,1,nil)
end
